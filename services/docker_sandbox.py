import docker
import asyncio
import time
import uuid
import tempfile
import os
import platform
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config import settings


class DockerSandbox:
    def __init__(self):
        self.client = None
        self.containers = {}  # Track active containers with TTL
        self.cleanup_task = None
        
        try:
            # Try multiple connection methods for Windows
            if platform.system() == "Windows":
                connection_methods = [
                    ('npipe:////./pipe/docker_engine', 'Named Pipe'),
                    ('tcp://localhost:2375', 'TCP localhost:2375'),
                    ('tcp://127.0.0.1:2375', 'TCP 127.0.0.1:2375'),
                ]
                
                for base_url, method_name in connection_methods:
                    try:
                        self.client = docker.DockerClient(base_url=base_url)
                        self.client.ping()
                        print(f"✓ Docker client initialized successfully using {method_name}")
                        break
                    except Exception as e:
                        continue
                
                if self.client is None:
                    raise Exception("Could not connect to Docker using any method")
            else:
                self.client = docker.from_env()
                self.client.ping()
                print("✓ Docker client initialized successfully")
                
        except Exception as e:
            print(f"⚠ Warning: Docker client initialization failed: {e}")
            print("  Code execution features will be disabled.")
            print("  Make sure Docker Desktop is running.")
            print("  You may need to enable 'Expose daemon on tcp://localhost:2375 without TLS'")
            print("  in Docker Desktop Settings > General")
            self.client = None

    async def start_cleanup_task(self):
        """Start background task to clean up expired containers"""
        if self.client and self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodically clean up expired containers"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            await self.cleanup_expired_containers()

    async def cleanup_expired_containers(self):
        """Remove containers that exceeded their TTL"""
        current_time = datetime.utcnow()
        expired = []

        for container_id, info in self.containers.items():
            if current_time > info["expires_at"]:
                expired.append(container_id)

        for container_id in expired:
            await self._remove_container(container_id)

    async def _remove_container(self, container_id: str):
        """Force remove a container"""
        try:
            if self.client:
                container = self.client.containers.get(container_id)
                container.stop(timeout=1)
                container.remove(force=True)
                print(f"Removed container: {container_id}")
        except Exception as e:
            print(f"Error removing container {container_id}: {e}")
        finally:
            if container_id in self.containers:
                del self.containers[container_id]

    async def execute_python_code(
        self, code: str, test_input: Optional[str] = None, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute Python code in a Docker container"""
        if not self.client:
            return {
                "success": False,
                "error": "Docker client not available",
                "output": None,
                "execution_time": 0,
            }

        timeout = timeout or settings.DOCKER_TIMEOUT
        container_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Create temporary file with code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Get the actual filename for Docker command
            temp_filename = os.path.basename(temp_file)
            
            # Create container
            container = self.client.containers.create(
                image="python:3.11-slim",
                command=["python", f"/code/{temp_filename}"],
                volumes={os.path.dirname(temp_file): {"bind": "/code", "mode": "ro"}},
                mem_limit=settings.DOCKER_MEMORY_LIMIT,
                cpu_quota=settings.DOCKER_CPU_QUOTA,
                network_mode="none",  # Disable network access
                detach=True,
                stdin_open=bool(test_input),
            )

            # Track container with TTL
            self.containers[container.id] = {
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow()
                + timedelta(seconds=settings.CONTAINER_TTL),
            }

            # Start container
            container.start()

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout)
                logs = container.logs(stdout=True, stderr=True).decode("utf-8")

                execution_time = time.time() - start_time

                # Check exit code
                exit_code = result.get("StatusCode", 1)

                if exit_code == 0:
                    return {
                        "success": True,
                        "output": logs,
                        "error": None,
                        "execution_time": execution_time,
                    }
                else:
                    return {
                        "success": False,
                        "output": logs,
                        "error": f"Process exited with code {exit_code}",
                        "execution_time": execution_time,
                    }

            except Exception as e:
                # Try to get logs even on timeout/error
                try:
                    logs = container.logs(stdout=True, stderr=True).decode("utf-8")
                except:
                    logs = None
                    
                return {
                    "success": False,
                    "output": logs,
                    "error": f"Execution timeout or error: {str(e)}",
                    "execution_time": time.time() - start_time,
                }

        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "execution_time": time.time() - start_time,
            }

        finally:
            # Cleanup
            try:
                container.stop(timeout=1)
                container.remove(force=True)
                if container.id in self.containers:
                    del self.containers[container.id]
            except:
                pass

            try:
                os.unlink(temp_file)
            except:
                pass

    async def execute_code_with_tests(
        self, code: str, test_cases: list
    ) -> Dict[str, Any]:
        """Execute code against multiple test cases"""
        results = []
        all_passed = True

        for i, test_case in enumerate(test_cases):
            # Prepare code with test case
            test_input = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")

            # Wrap code to capture test execution
            wrapped_code = f"""
import sys
import io
import json

# Test input (may be JSON string)
test_input_raw = '''{test_input}'''

# User's code
{code}

# Parse input and call solution
try:
    # Try to parse as JSON to handle quoted strings
    try:
        parsed_input = json.loads(test_input_raw)
    except:
        # If not JSON, use as-is
        parsed_input = test_input_raw
    
    # Call the solution function
    if isinstance(parsed_input, list):
        # Multiple arguments
        result = solution(*parsed_input)
    else:
        # Single argument
        result = solution(parsed_input)
    
    # Print result
    print(str(result).lower() if isinstance(result, bool) else result)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    raise
"""

            result = await self.execute_python_code(wrapped_code)

            if result["success"]:
                actual_output = result["output"].strip()
                expected = str(expected_output).strip()
                passed = actual_output == expected

                results.append(
                    {
                        "test_case": i + 1,
                        "passed": passed,
                        "input": test_input,
                        "expected": expected,
                        "actual": actual_output,
                        "execution_time": result["execution_time"],
                    }
                )

                if not passed:
                    all_passed = False
            else:
                results.append(
                    {
                        "test_case": i + 1,
                        "passed": False,
                        "input": test_input,
                        "expected": expected_output,
                        "error": result["error"],
                        "output": result.get("output"),  # Include actual output/traceback
                        "execution_time": result["execution_time"],
                    }
                )
                all_passed = False

        return {
            "success": all_passed,
            "test_results": results,
            "total_tests": len(test_cases),
            "passed_tests": sum(1 for r in results if r.get("passed", False)),
        }

    async def shutdown(self):
        """Cleanup all containers on shutdown"""
        if self.cleanup_task:
            self.cleanup_task.cancel()

        for container_id in list(self.containers.keys()):
            await self._remove_container(container_id)


# Singleton instance
docker_sandbox = DockerSandbox()
