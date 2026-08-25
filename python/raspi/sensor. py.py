# Import some modules that we need
import imrt_robot_serial
import signal
import time
import sys


# We want our program to send commands at 10 Hz (10 commands per second)
execution_frequency = 10 #Hz
execution_period = 1. / execution_frequency #seconds


# Create motor serial object
motor_serial = imrt_robot_serial.IMRTRobotSerial()


# Open serial port. Exit if serial port cannot be opened
try:
    motor_serial.connect("/dev/ttyACM0")
except:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

   
# Start serial receive thread
motor_serial.run()

# Time until robot stops turning and resumes normal driving
turn_until = 0.0
turn_duration = 1.34
# Now we will enter a loop that will keep looping until the program terminates
# The motor_serial object will inform us when it's time to exit the program
# (say if the program is terminated by the user)
print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now :


    ###############################################################
    # This is the start of our loop. Your code goes below.        #
    #                                                             #
    # An example is provided to give you a starting point         #
    # In this example we get the distance readings from each of   #
    # the two distance sensors. Then we multiply each reading     #
    # with a constant gain and use the two resulting numbers      #
    # as commands for each of the two motors.                     #
    #  ________________________________________________________   #
    # |                                                        |  #
    # V                                                           #
    # V                                                           #
    ###############################################################


    # Get the current time
    iteration_start_time = time.time()
    now = time.time()

    # Obstacle threshold in cm
    obstacle_threshold_cm = 15.0
    #turn_duration = 1.34

    # Get and print readings from distance sensors
    dist_1 = motor_serial.get_dist_1()
    dist_2 = motor_serial.get_dist_2()
    dist_3 = motor_serial.get_dist_3()
    dist_4 = motor_serial.get_dist_4()
    print("foran:", dist_1, " høyre:", dist_2, "venstre:", dist_3, "bak", dist_4)

    # Default forward motion
    speed_motor_1 = 120
    speed_motor_2 = 120

    # Keep turning for the remaining duration before resuming normal behavior
    if now < turn_until:
        speed_motor_1 = 60
        speed_motor_2 = -60

    # hindring foran på alle sensorer
    elif  dist_1 < obstacle_threshold_cm and dist_2< 30.0 and dist_3< 30.0:
        # snu rundt i en viss tid
        turn_until = now + turn_duration
        speed_motor_1 = 60
        speed_motor_2 = -60


    # Hindring rett fram: velg siden med størst avstand.
    elif dist_1<obstacle_threshold_cm:
        if dist_2 > dist_3:
            # Det er mest plass til høyre.
            speed_motor_1 = 120
            speed_motor_2 = -80

        else:
            # Det er mest plass til venstre.
            speed_motor_1 = -80
            speed_motor_2 = 120

    # Hindring foran til høyre: sving venstre.
    elif dist_2 < obstacle_threshold_cm and dist_2 < dist_3:
        speed_motor_1 = -80
        speed_motor_2 = 120

    # Hindring foran til venstre: sving høyre.
    elif dist_3 < obstacle_threshold_cm:
        speed_motor_1 = 120
        speed_motor_2 = -80

    # hindring foran, men langt unna
    elif dist_1 > obstacle_threshold_cm and dist_2 == dist_3:
        speed_motor_1 = 60
        speed_motor_2 = 60
   

   
    '''
    # If something is closer than 100 cm, react and steer away from it
    if dist_1 < obstacle_threshold_cm or dist_2 < obstacle_threshold_cm or dist_3 < obstacle_threshold_cm or dist_4 < obstacle_threshold_cm:
        if dist_1 < dist_2:
            # Object is closer on the left side => turn right
            speed_motor_1 = 120
            speed_motor_2 = -80
        elif dist_2 < dist_1:
            # Object is closer on the right side => turn left
            speed_motor_1 = -80
            speed_motor_2 = 120
        else:
            # Object straight ahead => reverse a little and turn
            speed_motor_1 = -100
            speed_motor_2 = -100
'''
    # Keep motor commands in valid range
    speed_motor_1 = max(-400, min(400, speed_motor_1))
    speed_motor_2 = max(-400, min(400, speed_motor_2))

    # Send commands to motor
    # Max speed is 400.
    # E.g. a command of 500 will result in the same speed as if the command was 400
    motor_serial.send_command(speed_motor_1, speed_motor_2)



    # Here we pause the execution of the program for the apropriate amout of time
    # so that our loop executes at the frequency specified by the variable execution_frequency
    iteration_end_time = time.time() # current time
    iteration_duration = iteration_end_time - iteration_start_time # time spent executing code
    if (iteration_duration < execution_period):
        time.sleep(execution_period - iteration_duration)



    ###############################################################
    #                                                           A #
    #                                                           A #
    # |_________________________________________________________| #
    #                                                             #
    # This is the end of our loop,                                #
    # execution continus at the start of our loop                 #
    ###############################################################
    ###############################################################





# motor_serial has told us that its time to exit
# we have now exited the loop
# It's only polite to say goodbye
print("Goodbye")