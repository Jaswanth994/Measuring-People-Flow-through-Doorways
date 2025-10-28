# main.py
import cv2
import time
import csv
from sensor import GridEYESensor
from processor import PeopleCounter
from config import *

# --- Logging Setup ---
LOG_FILE = os.path.join(DATA_DIR, "log_data.csv")
LOG_INTERVAL_FRAMES = FRAME_RATE # Log data once per second

def initialize_logger():
    """Initializes the CSV log file with headers."""
    headers = ['Timestamp_ms', 'Occupancy'] + [f'Pixel_{i}' for i in range(TOTAL_PIXELS)]
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

def log_data(timestamp, occupancy, frame_data):
    """Appends data to the CSV log file."""
    data_row = [timestamp, occupancy] + frame_data.tolist()
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data_row)

def main():
    initialize_logger()
    sensor = GridEYESensor()
    
    # Initialization Phase: Load or Determine Background
    if not sensor.load_background():
        if not sensor.determine_background():
            print("FATAL: Could not initialize sensor or determine background.")
            return
        sensor.save_background()
        
    counter = PeopleCounter(sensor.background)
    
    print("\n--- Starting Real-Time People Counting ---")
    print(f"Occupancy is tracked continuously (1 frame = {FRAME_DELAY_MS}ms). Press 'q' to exit.")
    
    frame_counter = 0
    
    # Main Real-Time Loop
    while True:
        start_time = time.time()
        
        # A. Read Sensor Data
        current_frame = sensor.get_current_frame()
        
        # B. Process Frame
        counter.process_frame(current_frame)

        # C. Logging (Every LOG_INTERVAL_FRAMES)
        if frame_counter % LOG_INTERVAL_FRAMES == 0:
            log_data(int(time.time() * 1000), counter.occupancy_count, current_frame)
            
        frame_counter += 1

        # D. Visualization
        display_mat = sensor.get_frame_mat(current_frame)
        
        # Normalize and apply color map
        cv2.normalize(display_mat, display_mat, 0, 255, cv2.NORM_MINMAX)
        display_mat_8u = display_mat.astype(np.uint8)
        display_colored = cv2.applyColorMap(display_mat_8u, cv2.COLORMAP_JET)
        
        # Draw status and detected body location
        status_text = f"Occupancy: {counter.occupancy_count} | Bodies Tracked: {len(counter.tracked_people)}"
        cv2.putText(display_colored, status_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
        for person in counter.tracked_people:
            # Draw a circle at the detected body's column location
            col_center = int((person.location_col + 0.5) * (320 / GRID_SIZE))
            
            # Color based on tracking status (Green for counted, Yellow for detected)
            color = (0, 255, 0) if person.counted else (0, 255, 255) 
            
            # Draw the detected center
            cv2.circle(display_colored, (col_center, 160), 10, color, -1)
            temp_text = f"ID:{person.id} T:{person.max_temp:.1f}C"
            cv2.putText(display_colored, temp_text, (col_center - 30, 280), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        cv2.imshow("GridEYE People Counter", display_colored)
        
        # E. Enforce Frame Rate and Exit Check
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
            
        elapsed_time = time.time() - start_time
        sleep_time = (1.0 / FRAME_RATE) - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()