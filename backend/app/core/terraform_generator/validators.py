"""Terraform HCL Validators.

Validiert generierte Terraform-Dateien mit terraform CLI.
"""

import logging
import subprocess
from pathlib import Path

from app.core.terraform_generator.exceptions import TerraformValidationError

logger = logging.getLogger(__name__)


class TerraformValidator:
    """Validiert Terraform HCL Code mit terraform CLI."""

    def __init__(self, terraform_binary: str = "terraform"):
        """Initialisiert Validator.

        Args:
            terraform_binary: Path zum terraform Binary (default: "terraform")
        """
        self.terraform_binary = terraform_binary

    def validate_syntax(self, hcl_code: str) -> tuple[bool, list[str]]:
        """Validiert HCL Syntax (einfache Checks ohne terraform CLI).

        Prüft auf offensichtliche Syntax-Fehler.

        Args:
            hcl_code: Terraform HCL Code

        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []

        # Prüfe auf balanced braces
        if hcl_code.count("{") != hcl_code.count("}"):
            errors.append("Unbalanced curly braces")

        # Prüfe auf balanced quotes (einfache Checks)
        quote_count = hcl_code.count('"')
        if quote_count % 2 != 0:
            errors.append("Unbalanced quotes")

        # Prüfe auf leere resource/data blocks
        if "resource \"\" \"\"" in hcl_code or 'resource "" ""' in hcl_code:
            errors.append("Empty resource type or name")

        return len(errors) == 0, errors

    def validate_directory(
        self,
        directory: Path,
        skip_init: bool = False
    ) -> tuple[bool, str, str]:
        """Validiert Terraform-Dateien in einem Verzeichnis.

        Führt `terraform init` und `terraform validate` aus.

        Args:
            directory: Verzeichnis mit .tf Dateien
            skip_init: Ob terraform init übersprungen werden soll

        Returns:
            Tuple (success, stdout, stderr)

        Raises:
            TerraformValidationError: Bei Validierungsfehlern
        """
        if not directory.exists():
            raise TerraformValidationError(f"Directory does not exist: {directory}")

        # Prüfe ob .tf Dateien existieren
        tf_files = list(directory.glob("*.tf"))
        if not tf_files:
            raise TerraformValidationError(f"No .tf files found in {directory}")

        # Terraform init (wenn nicht skip)
        if not skip_init:
            init_success, init_stdout, init_stderr = self._run_terraform_command(
                ["init", "-backend=false"],
                directory
            )
            if not init_success:
                logger.error(f"terraform init failed: {init_stderr}")
                raise TerraformValidationError(
                    "terraform init failed",
                    errors=[init_stderr]
                )

        # Terraform validate
        validate_success, validate_stdout, validate_stderr = self._run_terraform_command(
            ["validate"],
            directory
        )

        return validate_success, validate_stdout, validate_stderr

    def format_check(self, directory: Path) -> tuple[bool, str]:
        """Prüft Terraform Formatting mit `terraform fmt`.

        Args:
            directory: Verzeichnis mit .tf Dateien

        Returns:
            Tuple (is_formatted, diff_output)
        """
        success, stdout, stderr = self._run_terraform_command(
            ["fmt", "-check", "-diff"],
            directory
        )

        # fmt -check returns exit code 3 if formatting changes are needed
        # exit code 0 = already formatted
        # exit code 3 = formatting needed
        return success, stdout

    def _run_terraform_command(
        self,
        args: list[str],
        working_dir: Path,
        timeout: int = 120
    ) -> tuple[bool, str, str]:
        """Führt terraform Kommando aus.

        Args:
            args: Terraform Argumente (z.B. ["validate"])
            working_dir: Working Directory
            timeout: Timeout in Sekunden

        Returns:
            Tuple (success, stdout, stderr)
        """
        cmd = [self.terraform_binary] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            logger.error(f"Terraform command timed out: {' '.join(cmd)}")
            return False, "", f"Command timed out after {timeout}s"

        except FileNotFoundError:
            logger.error(f"Terraform binary not found: {self.terraform_binary}")
            return False, "", f"Terraform binary not found: {self.terraform_binary}"

        except Exception as e:
            logger.error(f"Error running terraform command: {e}")
            return False, "", str(e)

    def check_terraform_installed(self) -> tuple[bool, str | None]:
        """Prüft ob Terraform installiert ist und gibt Version zurück.

        Returns:
            Tuple (is_installed, version_string)
        """
        try:
            result = subprocess.run(
                [self.terraform_binary, "version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )

            if result.returncode == 0:
                # Parse version from output (first line)
                version = result.stdout.split("\n")[0]
                return True, version

            return False, None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False, None
