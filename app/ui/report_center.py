from __future__ import annotations

"""
Purpose:
    Non-modal report generation center.

Used By:
    MainWindow

Responsibilities:
    - Display available reports.
    - Let the user choose one or more reports.
    - Let the user choose CSV/PDF output.
    - Let the user include/exclude empty reports.
    - Let the user override the output folder.
    - Generate selected reports.
    - Show generation progress and results.

Notes:
    This window should not build report content directly.
    Report content belongs inside report classes.
"""

from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox

import customtkinter as ctk

from app.reports.report_utils import get_date_folder
from app.reports.report_utils import archive_existing_reports


class ReportCenter(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        report_registry,
        app_state,
        base_output_folder: Path,
    ) -> None:
        super().__init__(parent)

        self.report_registry = report_registry
        self.app_state = app_state
        self.base_output_folder = Path(base_output_folder)

        self.title("Report Center")
        self.geometry("720x620")
        self.minsize(680, 560)

        self.report_vars: dict[str, ctk.BooleanVar] = {}
        self.csv_var = ctk.BooleanVar(value=True)
        self.pdf_var = ctk.BooleanVar(value=False)
        self.include_empty_var = ctk.BooleanVar(value=False)

        self.output_folder_var = ctk.StringVar(
            value=str(
                get_date_folder(
                    release=self.app_state.release,
                    base_path=self.base_output_folder,
                )
            )
        )

        self.progress_var = ctk.DoubleVar(value=0)
        self.current_report_var = ctk.StringVar(value="Ready")
        self.results_var = ctk.StringVar(value="")

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Report Center",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        body = ctk.CTkFrame(self, corner_radius=10)
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=8)
        body.grid_columnconfigure(0, weight=1)

        self._build_report_selection(body)
        self._build_output_options(body)
        self._build_progress_area(body)

        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 18))

        ctk.CTkButton(
            button_bar,
            text="Generate Selected",
            command=self.generate_selected,
            width=160,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_bar,
            text="Close",
            command=self.destroy,
            width=120,
        ).pack(side="right")

    def _build_report_selection(
        self,
        parent,
    ) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=8)
        frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Available Reports",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        ctk.CTkButton(
            frame,
            text="Select All Reports",
            command=self.select_all_reports,
            width=160,
        ).grid(row=0, column=1, sticky="e", padx=12, pady=(10, 4))

        for row_index, report_name in enumerate(
            self.report_registry.get_names(), start=1
        ):
            var = ctk.BooleanVar(value=True)
            self.report_vars[report_name] = var

            ctk.CTkCheckBox(
                frame,
                text=report_name,
                variable=var,
            ).grid(row=row_index, column=0, columnspan=2, sticky="w", padx=18, pady=3)

    def _build_output_options(
        self,
        parent,
    ) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=8)
        frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="Output",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        ctk.CTkCheckBox(
            frame,
            text="CSV",
            variable=self.csv_var,
        ).grid(row=1, column=0, sticky="w", padx=18, pady=4)

        ctk.CTkCheckBox(
            frame,
            text="PDF where supported",
            variable=self.pdf_var,
        ).grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ctk.CTkCheckBox(
            frame,
            text="Include Empty Reports",
            variable=self.include_empty_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=4)

        ctk.CTkLabel(
            frame,
            text="Folder",
        ).grid(row=3, column=0, sticky="w", padx=18, pady=(10, 4))

        ctk.CTkEntry(
            frame,
            textvariable=self.output_folder_var,
        ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=(18, 8), pady=(0, 12))

        ctk.CTkButton(
            frame,
            text="Browse...",
            command=self.browse_folder,
            width=100,
        ).grid(row=4, column=2, sticky="e", padx=(0, 18), pady=(0, 12))

    def _build_progress_area(
        self,
        parent,
    ) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=8)
        frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Progress",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(
            frame,
            variable=self.progress_var,
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=18, pady=(4, 8))
        self.progress_bar.set(0)

        ctk.CTkLabel(
            frame,
            textvariable=self.current_report_var,
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))

        self.results_label = ctk.CTkLabel(
            frame,
            textvariable=self.results_var,
            justify="left",
            anchor="w",
        )
        self.results_label.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 12))

    def select_all_reports(
        self,
    ) -> None:
        for var in self.report_vars.values():
            var.set(True)

    def browse_folder(
        self,
    ) -> None:
        selected = filedialog.askdirectory(
            title="Choose report output folder",
            initialdir=self.output_folder_var.get(),
        )

        if selected:
            self.output_folder_var.set(selected)

    def get_selected_reports(
        self,
    ) -> list[str]:
        return [
            report_name for report_name, var in self.report_vars.items() if var.get()
        ]

    def get_selected_formats(
        self,
    ) -> list[str]:
        formats: list[str] = []

        if self.csv_var.get():
            formats.append("csv")

        if self.pdf_var.get():
            formats.append("pdf")

        return formats

    def generate_selected(
        self,
    ) -> None:
        report_names = self.get_selected_reports()
        formats = self.get_selected_formats()

        if not report_names:
            messagebox.showwarning(
                "No Reports Selected",
                "Select at least one report.",
            )
            return

        if not formats:
            messagebox.showwarning(
                "No Output Format Selected",
                "Select CSV, PDF, or both.",
            )
            return

        output_folder = Path(self.output_folder_var.get())
        output_folder.mkdir(parents=True, exist_ok=True)

        archive_existing_reports(output_folder)

        total_steps = len(report_names) * len(formats)
        completed_steps = 0
        generated_files: list[Path] = []

        self.progress_bar.set(0)
        self.results_var.set("")

        for report_name in report_names:
            for output_format in formats:
                self.current_report_var.set(
                    f"Generating {report_name} ({output_format.upper()})..."
                )
                self.update_idletasks()

                try:
                    output_path = self.report_registry.generate(
                        name=report_name,
                        output_format=output_format,
                        state=self.app_state,
                        output_folder=output_folder,
                        include_empty=self.include_empty_var.get(),
                    )

                    if output_path is not None:
                        generated_files.append(output_path)

                except NotImplementedError:
                    # Some reports may not support PDF yet.
                    pass

                completed_steps += 1
                self.progress_bar.set(completed_steps / total_steps)
                self.update_idletasks()

        self.current_report_var.set("Complete")

        if generated_files:
            result_text = "Generated:\n" + "\n".join(
                f"✓ {path.name}" for path in generated_files
            )
        else:
            result_text = "No report files were generated."

        self.results_var.set(result_text)
