import asyncio
from contextlib import suppress
import sys
import cv2

from control_logic.motor_control.poweredup_control import poweredup_control

# size of centered rectangle a proportion of width/height
C_AREA_X = 0.1
C_AREA_Y = 0.1


# used for powered up control to invert motor
PU_X_MULT = -1
PU_Y_MULT = -1

DEBUG = True
WEBCAM_INDEX = 1

# Initialize the camera

def dummy_move_camera(x, y):
    print(f"direction to move: ({x}, {y})")


def get_video_dimensions(cap):
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    return (width, height)

def get_center_area_coords(cap):
    # returns (x1, y1), (x2, y2)
    width, height = get_video_dimensions(cap)
    edge_percent_x = ((1 - C_AREA_X) / 2)
    edge_percent_y = ((1 - C_AREA_Y) / 2)
    top_left = (round(edge_percent_x * width), round(edge_percent_y * height))
    bottom_right = (round((1 - edge_percent_x) * width), round((1 - edge_percent_y) * height))
    return top_left, bottom_right

def get_rect_center(top_left, bottom_right):
    x = int((top_left[0] + bottom_right[0])/2)
    y = int((top_left[1] + bottom_right[1])/2)
    return (x, y)



def detect(gray, frame):
    # returns a frame with a rectangle drawn, and the rectangle corners for first face
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_frontalface_default.xml') 
     # detect a face
    faces = face_cascade.detectMultiScale(gray, scaleFactor= 1.5, minNeighbors=2)
    for (x, y, w, h) in faces:
        top_left = (x, y)
        bottom_right = ((x + w), (y + h))
        cv2.rectangle(frame, top_left, bottom_right, (255, 255, 0), 4)
        cv2.circle(frame, get_rect_center(top_left, bottom_right), 4, (0, 255, 0), -1)
        # single face for now, so return values from here
        return frame, top_left, bottom_right

    #currently not used as multiple faces aren't being support for now     
    return frame, None, None

def check_face_in_center(top_left, bottom_right, cap):
    # just using the center of face to check if it is within center area
    c_top_left, c_bottom_right = get_center_area_coords(cap)
    face_center = get_rect_center(top_left, bottom_right)
    x_axis = face_center[0] >= c_top_left[0] and face_center[0] <= c_bottom_right[0]
    y_axis = face_center[1] >= c_top_left[1] and face_center[1] <= c_bottom_right[1]
    return x_axis and y_axis


    

async def camera_center_face(top_left, bottom_right, cap, move_camera):
    # move the camera incrementally so that the face ends up in the center area
    if bottom_right is None or check_face_in_center(top_left, bottom_right, cap):
        # if face is already around the center, no need to do anything
        return
    c_top_left, c_bottom_right = get_center_area_coords(cap)
    f_center = get_rect_center(top_left, bottom_right)
    # these values will be manipulated.
    x_move = 0
    y_move = 0

    if f_center[0] > c_bottom_right[0]:
        x_move = -1
    elif f_center[0] < c_top_left[0]:
        x_move = 1
    
    if f_center[1] > c_bottom_right[1]:
        y_move = -1
    elif f_center[1] < c_top_left[1]:
        y_move = 1

    await move_camera(x_move, y_move)
    


# When everything done, release the capture


async def main():
    print("Creating controls")
    controls = await poweredup_control.create()
    if controls is None:
        print("not connected")
        return()
    async def poweredup_move_camera(x, y):
        power = 600
        degmult = 10
        await controls.sendCmd(f"(A, {power}, {x * degmult * PU_X_MULT})|(B, {power}, {y * degmult * PU_Y_MULT})")
        #asyncio.create_task(controls.sendCmd(f"(A, {power}, {x * degmult * PU_X_MULT})|(B, {power}, {y * degmult * PU_Y_MULT})"))
    move_camera = poweredup_move_camera

    print("Initialising Video Capture")
    cap = cv2.VideoCapture(WEBCAM_INDEX)  # 0 is the index of the built-in webcam, change if you have multiple cameras
    # Check if the camera opened successfully
    if not cap.isOpened():
        print("Error opening video stream or file")    



    # Read an image from the camera
    center_area_coords = get_center_area_coords(cap)
    while True:
        ret, frame = cap.read()
        if ret:
            # Frame is successfully read
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            new_frame, face_top_left, face_bottom_right = detect(gray, frame)
            if DEBUG:
                new_frame = cv2.rectangle(new_frame, center_area_coords[0], center_area_coords[1], (255, 120, 255), 4)
                if face_top_left is not None and not check_face_in_center(face_top_left, face_bottom_right, cap):
                    new_frame = cv2.putText(new_frame, "NOT CENTERED", (150,150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 2, cv2.LINE_4)
                if face_top_left is None:
                    new_frame = cv2.putText(new_frame, "NO FACE", (150,150), cv2.FONT_HERSHEY_SIMPLEX,  2, (0, 255, 255), 2, cv2.LINE_4)
            await camera_center_face(face_top_left, face_bottom_right, cap, move_camera)
            
            cv2.imshow('Captured Image', new_frame) # Wait for a key press to close the window
        else:
            print("Failed to capture image")
        if cv2.waitKey(10) & 0xFF == ord('q'):
                break




    cap.release()
    cv2.destroyAllWindows()
    pass


# Run the main async program.
if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())