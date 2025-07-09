import cv2
from deepface import DeepFace
import os

# Create a directory to store captured images if it doesn't exist
if not os.path.exists("captured_faces"):
    os.makedirs("captured_faces")

def capture_and_verify():
    cap = cv2.VideoCapture(0) # 0 for default webcam

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    img_count = 0
    captured_images = []

    print("Press 's' to capture an image. Capture two images for verification.")
    print("Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Display the live feed
        cv2.imshow('Webcam - Press "s" to capture, "q" to quit', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            img_name = f"captured_faces/face_{img_count}.jpg"
            cv2.imwrite(img_name, frame)
            captured_images.append(img_name)
            print(f"Image {img_count + 1} captured: {img_name}")
            img_count += 1

            if len(captured_images) == 2:
                img1_path = captured_images[0]
                img2_path = captured_images[1]

                try:
                    # Perform face verification
                    result = DeepFace.verify(img1_path=img1_path, img2_path=img2_path)

                    if result["verified"]:
                        print("\nVerification Result: SAME PERSON!")
                    else:
                        print("\nVerification Result: DIFFERENT PERSON!")
                    print(f"Distance: {result['distance']:.4f}, Threshold: {result['threshold']:.4f}")
                    print("-" * 30)

                    # Reset for next verification
                    captured_images = []
                    img_count = 0
                    print("Ready for next verification. Capture two new images.")

                except Exception as e:
                    print(f"\nError during DeepFace verification: {e}")
                    print("Make sure a face is clearly visible in both captured images.")
                    # Optionally clear captured images if verification fails
                    # captured_images = []
                    # img_count = 0
                
                # To avoid re-verification with the same images if 's' is pressed repeatedly after 2 images
                # You might want to remove the files or simply reset the list.
                # For this example, we'll reset the list and keep the files.


        elif key == ord('q'):
            print("Quitting...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_verify()