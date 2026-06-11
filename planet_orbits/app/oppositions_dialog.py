"""Dialog to display computed oppositions in a table."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class OppositionsDialog(QDialog):
    """Show opposition rows with date, series length, and a plot checkbox."""

    def __init__(self, planet_name, oppositions, series_lengths, plot_flags, parent=None):
        """Initialize the dialog with opposition data.
        
        Parameters
        ----------
        planet_name : str
        Name of the planet for which oppositions are shown.
        
        oppositions : list of datetime
        List of opposition dates.
        
        series_lengths : list of int
        List of series lengths corresponding to each opposition.
        
        plot_flags : list of bool
        List of flags indicating which series to plot.
        
        parent : QWidget, optional
        Parent widget for the dialog.
        """
        super().__init__(parent)

        self.setWindowTitle(f"Oppositions for {planet_name.capitalize()}")
        self.resize(700, 450)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Found {len(oppositions)} oppositions."))

        self.table = QTableWidget(len(oppositions), 3)
        self.table.setHorizontalHeaderLabels(["Date", "Yearly Series Length", "Plot"])
        self.table.verticalHeader().setVisible(False)
        self.plot_checkboxes = []

        toggle_all_button = QPushButton("Check/Uncheck All Plot")
        toggle_all_button.clicked.connect(self._toggle_all_plot_flags)
        layout.addWidget(toggle_all_button)

        for row, (opposition, series_length, plot_flag) in enumerate(zip(oppositions, series_lengths, plot_flags)):
            date_item = QTableWidgetItem(opposition.strftime("%Y-%m-%d %H:%M:%S"))
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, date_item)

            series_item = QTableWidgetItem(str(series_length))
            series_item.setFlags(series_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            series_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, series_item)

            plot_checkbox = QCheckBox("Plot")
            plot_checkbox.setChecked(plot_flag)
            self.plot_checkboxes.append(plot_checkbox)
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.addWidget(plot_checkbox)
            self.table.setCellWidget(row, 2, checkbox_container)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def selected_rows_to_plot(self):
        """Return a flag list indicating which oppositions are selected for plotting."""
        return [checkbox.isChecked() for checkbox in self.plot_checkboxes]

    def _toggle_all_plot_flags(self):
        """Toggle all plot checkboxes at once."""
        should_check_all = not all(checkbox.isChecked() for checkbox in self.plot_checkboxes)
        for checkbox in self.plot_checkboxes:
            checkbox.setChecked(should_check_all)
