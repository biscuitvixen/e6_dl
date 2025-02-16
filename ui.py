import time
import threading
import queue
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE

class ImagePoolDownloaderUI:
    def __init__(self):
        self.console = Console()
        
        # Queues for managing pools and images
        self.pool_queue = queue.Queue()  # Holds pool IDs
        self.current_pool = None  # Currently processing pool ID
        self.image_status = {}  # Dictionary to track image download statuses
        
        # Thread management
        self.running = True
        self.lock = threading.Lock()  # Lock for thread-safe UI updates
        
        # Start UI refresh thread
        self.ui_thread = threading.Thread(target=self.run_ui, daemon=True)
        self.ui_thread.start()

        # Start user input thread
        self.input_thread = threading.Thread(target=self.user_input_loop, daemon=True)
        self.input_thread.start()

    def run_ui(self):
        """Runs the Rich Live UI."""
        with Live(self.render_layout(), refresh_per_second=4, screen=True) as live:
            while self.running:
                live.update(self.render_layout())
                time.sleep(0.5)

    def render_layout(self):
        """Creates the UI layout."""
        layout = Table.grid(expand=True)
        
        # Pool Queue Panel
        queue_panel = self.render_queue_panel()
        layout.add_row(queue_panel)

        # Current Pool Panel
        image_panel = self.render_image_panel()
        layout.add_row(image_panel)

        # User Input Panel
        input_panel = self.render_input_panel()
        layout.add_row(input_panel)

        return layout

    def render_queue_panel(self):
        """Renders the queue of pools waiting for download."""
        table = Table(title="📥 Pool Queue", header_style="bold magenta", box=SIMPLE)
        table.add_column("Pool ID", justify="center")

        # Display pool IDs in queue
        with self.lock:
            if self.pool_queue.empty():
                table.add_row("[dim]No pools in queue[/dim]")
            else:
                for pool_id in list(self.pool_queue.queue):
                    table.add_row(str(pool_id))

        return Panel(table, border_style="magenta")

    def render_image_panel(self):
        """Renders the list of images in the currently downloading pool."""
        table = Table(title="📸 Downloading Images", header_style="bold cyan", box=SIMPLE)
        table.add_column("Image Name", justify="left")
        table.add_column("Status", justify="right")

        with self.lock:
            if not self.current_pool:
                table.add_row("[dim]No active pool[/dim]", "")
            else:
                for image_name, status in self.image_status.items():
                    status_text = self.get_status_text(status)
                    table.add_row(image_name, status_text)

        return Panel(table, border_style="cyan")

    def render_input_panel(self):
        """Renders the user input section."""
        input_text = Text("📝 Enter a pool ID to add to queue and press Enter", style="bold yellow")
        return Panel(input_text, border_style="yellow")

    def get_status_text(self, status):
        """Formats status text with colors."""
        status_colors = {
            "queued": "[blue]Queued[/blue]",
            "downloading": "[cyan]Downloading[/cyan]",
            "completed": "[green]Completed[/green]",
            "failed": "[red]Failed[/red]"
        }
        return status_colors.get(status, "[white]Unknown[/white]")

    def add_pool(self, pool_id):
        """Adds a pool to the queue."""
        with self.lock:
            self.pool_queue.put(pool_id)

    def start_next_pool(self):
        """Starts downloading images from the next pool in the queue."""
        with self.lock:
            if self.pool_queue.empty():
                self.current_pool = None
                return False

            self.current_pool = self.pool_queue.get()
            self.image_status.clear()

        return True

    def load_images_for_pool(self, image_names):
        """Loads image names into the tracking dictionary with 'queued' status."""
        with self.lock:
            for image_name in image_names:
                self.image_status[image_name] = "queued"

    def update_image_status(self, image_name, status):
        """Updates the status of an image."""
        with self.lock:
            if image_name in self.image_status:
                self.image_status[image_name] = status

    def user_input_loop(self):
        """Handles user input for adding pools."""
        while self.running:
            try:
                pool_id = Prompt.ask("[bold yellow]Enter Pool ID[/bold yellow]")
                if pool_id.isdigit():
                    self.add_pool(int(pool_id))
                    self.console.log(f"[green]Added Pool ID {pool_id} to queue.[/green]")
                else:
                    self.console.log("[red]Invalid Pool ID. Please enter numbers only.[/red]")
            except KeyboardInterrupt:
                self.running = False
                break

    def stop(self):
        """Stops the UI and threads safely."""
        self.running = False
        self.ui_thread.join()
        self.input_thread.join()

# Example Usage
if __name__ == "__main__":
    ui = ImagePoolDownloaderUI()
    
    # Simulating the downloader behavior
    def downloader_simulation():
        while True:
            if ui.start_next_pool():
                ui.console.log(f"[bold cyan]Started downloading Pool {ui.current_pool}[/bold cyan]")
                
                # Simulating image list
                image_names = [f"image_{i}.jpg" for i in range(1, 6)]
                ui.load_images_for_pool(image_names)

                for image in image_names:
                    time.sleep(2)  # Simulating API restriction
                    ui.update_image_status(image, "downloading")
                    time.sleep(2)
                    ui.update_image_status(image, "completed")

                ui.console.log(f"[bold green]Completed Pool {ui.current_pool}[/bold green]")

            time.sleep(1)  # Wait before checking the queue again

    # Start the downloader simulation in a separate thread
    threading.Thread(target=downloader_simulation, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ui.stop()
