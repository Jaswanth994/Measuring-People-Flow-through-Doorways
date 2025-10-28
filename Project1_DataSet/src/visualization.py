# src/visualization.py

import matplotlib.pyplot as plt
import os

def save_visualization(output_dir, frame_number, frame, foreground, final_blobs, est_count, actual_count, timestamp):
    """
    Saves the visualization of a single frame to a file.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Timestamp: {timestamp}')

    # 1. Raw Thermal Data
    im1 = axes[0].imshow(frame, cmap='inferno', vmin=25, vmax=35)
    axes[0].set_title('Raw Thermal Data')
    fig.colorbar(im1, ax=axes[0])

    # 2. Foreground
    axes[1].imshow(foreground, cmap='gray')
    axes[1].set_title('Foreground')

    # 3. Final Detections
    axes[2].imshow(final_blobs, cmap='viridis')
    axes[2].set_title(f'Detected People: {est_count} (Actual: {actual_count})')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the figure to a file
    file_name = f"frame_{frame_number:04d}.png"
    output_path = os.path.join(output_dir, file_name)
    plt.savefig(output_path)
    
    # Close the plot to free up memory
    plt.close(fig)