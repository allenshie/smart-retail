import os
import cv2
import argparse
from src.services.detect.experienceAreaDetection import ExperienceAreaDetection
from src.services.video.videoWriteService import VideoWriteService
from src.views.view import View

experienceArea_object_model = ExperienceAreaDetection()
view = View()

def process_video(source, output_dir, experienceArea_object_model, products_of_interest):
    cameraId = os.path.basename(source)
    cap = cv2.VideoCapture(source)
    out = VideoWriteService(cap=cap, output_path=os.path.join(output_dir, os.path.basename(source)))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        chairs, pillows, persons, frame = experienceArea_object_model.detect(
            cameraId=cameraId, 
            image=frame, 
            products_of_interest=products_of_interest
        )
        out.write(frame=frame)

    cap.release()
    # out.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Video inference tool')
    parser.add_argument('--video', type=str, default=None, help='Path to a single video file for inference')
    parser.add_argument('--videos', type=str, default=None, help='Path to a directory containing video files for inference')
    parser.add_argument('--output', type=str, default='output', help='Directory to save output videos')
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)

    products_of_interest = ['hands', 'pinto', 'balance_on', 'cosios', 'doctor_air']

    if args.video:
        # Process a single video file
        if not os.path.isfile(args.video):
            print(f"Error: The video path '{args.video}' does not exist.")
        else:
            print(f"Processing video: {args.video}")
            process_video(args.video, args.output, experienceArea_object_model, products_of_interest)

    elif args.videos:
        # Process all video files in the specified directory
        if not os.path.isdir(args.videos):
            print(f"Error: The directory path '{args.videos}' does not exist.")
        else:
            video_files = [os.path.join(args.videos, f) for f in os.listdir(args.videos) if f.endswith(('.mp4', '.avi', '.mov'))]
            if not video_files:
                print(f"No video files found in directory: {args.videos}")
            else:
                for video_file in video_files:
                    print(f"Processing video: {video_file}")
                    process_video(video_file, args.output, experienceArea_object_model, products_of_interest)

    else:
        print("Error: Please specify either --video or --videos parameter.")
    
