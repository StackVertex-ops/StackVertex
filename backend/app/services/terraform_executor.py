"""Terraform CLI Executor.

Wrapper für Terraform CLI Commands.
"""

import logging
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result von Terraform Command Execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str


class TerraformExecutor:
    """Executes Terraform CLI Commands."""

    def __init__(
        self,
        working_dir: Path,
        terraform_binary: str = "terraform",
        env_vars: Optional[Dict[str, str]] = None
    ):
        """Initialisiert Executor.

        Args:
            working_dir: Working Directory mit Terraform Files
            terraform_binary: Path zum Terraform Binary
            env_vars: Environment Variables (z.B. AWS Credentials)
        """
        self.working_dir = working_dir
        self.terraform_binary = terraform_binary
        self.env_vars = env_vars or {}

        logger.info(f"TerraformExecutor initialized for {working_dir}")

    def init(self, backend_config: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Führt terraform init aus.

        Args:
            backend_config: Backend Configuration (optional)

        Returns:
            ExecutionResult
        """
        args = ["init", "-input=false"]

        if backend_config:
            for key, value in backend_config.items():
                args.append(f"-backend-config={key}={value}")

        return self._run_command(args)

    def validate(self) -> ExecutionResult:
        """Führt terraform validate aus.

        Returns:
            ExecutionResult
        """
        return self._run_command(["validate"])

    def plan(
        self,
        var_file: Optional[Path] = None,
        out_file: Optional[Path] = None
    ) -> ExecutionResult:
        """Führt terraform plan aus.

        Args:
            var_file: Path zu .tfvars File (optional)
            out_file: Path für Plan Output (optional)

        Returns:
            ExecutionResult
        """
        args = ["plan", "-input=false"]

        if var_file:
            args.append(f"-var-file={var_file}")

        if out_file:
            args.append(f"-out={out_file}")

        return self._run_command(args)

    def apply(
        self,
        plan_file: Optional[Path] = None,
        auto_approve: bool = False
    ) -> ExecutionResult:
        """Führt terraform apply aus.

        Args:
            plan_file: Path zu Plan File (optional)
            auto_approve: Auto-approve ohne Confirmation

        Returns:
            ExecutionResult
        """
        args = ["apply", "-input=false"]

        if auto_approve:
            args.append("-auto-approve")

        if plan_file:
            args.append(str(plan_file))

        return self._run_command(args, timeout=1800)  # 30 min timeout

    def destroy(self, auto_approve: bool = False) -> ExecutionResult:
        """Führt terraform destroy aus.

        Args:
            auto_approve: Auto-approve ohne Confirmation

        Returns:
            ExecutionResult
        """
        args = ["destroy", "-input=false"]

        if auto_approve:
            args.append("-auto-approve")

        return self._run_command(args, timeout=1800)

    def output(self, format: str = "json") -> ExecutionResult:
        """Führt terraform output aus.

        Args:
            format: Output Format (json, raw)

        Returns:
            ExecutionResult
        """
        args = ["output"]

        if format == "json":
            args.append("-json")

        return self._run_command(args)

    def version(self) -> ExecutionResult:
        """Gibt Terraform Version zurück.

        Returns:
            ExecutionResult
        """
        return self._run_command(["version"])

    def _run_command(
        self,
        args: List[str],
        timeout: int = 600
    ) -> ExecutionResult:
        """Führt Terraform Command aus.

        Args:
            args: Command Arguments
            timeout: Timeout in Sekunden

        Returns:
            ExecutionResult
        """
        cmd = [self.terraform_binary] + args
        cmd_str = " ".join(cmd)

        logger.info(f"Executing: {cmd_str}")

        try:
            # Prepare environment
            import os
            env = os.environ.copy()
            env.update(self.env_vars)

            # Run command
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )

            success = result.returncode == 0

            if success:
                logger.info(f"Command succeeded: {cmd_str}")
            else:
                logger.warning(
                    f"Command failed with exit code {result.returncode}: {cmd_str}"
                )

            return ExecutionResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                command=cmd_str,
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                exit_code=-1,
                command=cmd_str,
            )

        except FileNotFoundError:
            logger.error(f"Terraform binary not found: {self.terraform_binary}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Terraform binary not found: {self.terraform_binary}",
                exit_code=-1,
                command=cmd_str,
            )

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                command=cmd_str,
            )
