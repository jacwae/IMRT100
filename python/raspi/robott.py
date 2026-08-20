# ============================================================
# ROBUST MAZE NAVIGATION - IMRT100
#
# Antakelse:
#   dist_1 = sensor foran
#   dist_2 = sensor mot høyre
#
# Strategi:
#   Høyrehåndsregelen
#
# Prioritet:
#   1. Høyre åpen -> sving høyre
#   2. Vegg foran -> sving venstre
#   3. Ellers -> følg høyre vegg
#
# Viktige forbedringer:
#   - medianfilter
#   - ugyldige målinger ignoreres
#   - filter resettes etter sving
#   - blindveier håndteres
#   - samme høyreåpning kan ikke trigges flere ganger
#   - roboten stopper hvis sensorene svikter
# ============================================================

import imrt_robot_serial
import time
import sys
import statistics


# ============================================================
# KONFIGURASJON
# ============================================================

LOOP_FREQUENCY = 10
LOOP_PERIOD = 1.0 / LOOP_FREQUENCY


# ---------------- MOTOR ----------------

FORWARD_SPEED = 90
TURN_SPEED = 85

MAX_SPEED = 180
MIN_FORWARD_SPEED = 50


# ---------------- AVSTANDER ----------------
#
# Disse verdiene må kalibreres på den ekte roboten.
#
# NB:
# Avstanden måles fra SENSORPLASSERINGEN,
# ikke fra robotens sentrum.

FRONT_STOP_DISTANCE = 30

TARGET_WALL_DISTANCE = 22

# Høyre regnes som åpen
RIGHT_OPEN_DISTANCE = 50

# Når høyresensoren igjen finner en vegg
# under denne verdien, kan en ny høyresving tillates.
RIGHT_WALL_FOUND_DISTANCE = 38


# ---------------- VEGGFØLGING ----------------

WALL_GAIN = 1.5

# Maksimal korreksjon hindrer roboten i å
# gjøre ekstremt brå utslag.
MAX_CORRECTION = 35


# ---------------- SVINGER ----------------
#
# Disse er tidsbaserte og MÅ kalibreres.

TURN_90_TIME = 0.80


# Hvor lenge roboten maksimalt får kjøre
# inn i et kryss før høyresving.

MAX_INTERSECTION_ADVANCE_TIME = 0.30


# ---------------- SENSORFILTER ----------------

FILTER_SIZE = 3

# Sensorverdier utenfor dette området
# blir betraktet som ugyldige.
MIN_VALID_DISTANCE = 1
MAX_VALID_DISTANCE = 300

# Etter så mange ugyldige sensorlesninger
# på rad stopper roboten.
MAX_INVALID_READS = 5


# ============================================================
# OPPSETT
# ============================================================

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyACM0")

except:
    print("Could not open port. Is your robot connected?")
    sys.exit()


motor_serial.run()


# ============================================================
# TILSTAND
# ============================================================

front_history = []
right_history = []

last_valid_front = None
last_valid_right = None

invalid_front_count = 0
invalid_right_count = 0


# Viktig:
#
# Etter at roboten har tatt en høyresving,
# settes denne til False.
#
# Den blir ikke True igjen før roboten faktisk
# finner en høyrevegg.
#
# Dette hindrer roboten i å spinne rundt
# i store åpne områder.

right_turn_armed = True


# ============================================================
# GENERELLE HJELPEFUNKSJONER
# ============================================================

def limit(value, minimum, maximum):

    return max(
        minimum,
        min(maximum, value)
    )


def valid_distance(value):

    """
    Returnerer True hvis sensorverdien ser gyldig ut.
    """

    try:
        value = float(value)

    except:
        return False

    return (
        MIN_VALID_DISTANCE
        <= value
        <= MAX_VALID_DISTANCE
    )


# ============================================================
# MOTORFUNKSJONER
# ============================================================

def stop_robot(duration=0.2):

    iterations = max(
        1,
        int(duration * LOOP_FREQUENCY)
    )

    for _ in range(iterations):

        motor_serial.send_command(
            0,
            0
        )

        time.sleep(LOOP_PERIOD)


def drive(left_speed, right_speed, duration):

    iterations = max(
        1,
        int(duration * LOOP_FREQUENCY)
    )

    left_speed = limit(
        left_speed,
        -MAX_SPEED,
        MAX_SPEED
    )

    right_speed = limit(
        right_speed,
        -MAX_SPEED,
        MAX_SPEED
    )

    for _ in range(iterations):

        motor_serial.send_command(
            left_speed,
            right_speed
        )

        time.sleep(LOOP_PERIOD)


# ============================================================
# SENSORFILTER
# ============================================================

def reset_sensor_filter():

    """
    Må kalles etter en sving.

    Gamle målinger kan ikke brukes etter en sving,
    fordi sensoren nå peker i en annen retning.
    """

    front_history.clear()
    right_history.clear()


def read_sensors():

    """
    Leser begge sensorene.

    Ugyldige målinger blir IKKE gjort til 999.
    I stedet brukes siste gyldige verdi.

    Hvis sensoren feiler for mange ganger på rad,
    returnerer vi None slik at roboten kan stoppe.
    """

    global last_valid_front
    global last_valid_right

    global invalid_front_count
    global invalid_right_count


    raw_front = motor_serial.get_dist_1()
    raw_right = motor_serial.get_dist_2()


    # ========================================================
    # FRONT
    # ========================================================

    if valid_distance(raw_front):

        front = float(raw_front)

        last_valid_front = front
        invalid_front_count = 0

    else:

        invalid_front_count += 1

        front = last_valid_front


    # ========================================================
    # RIGHT
    # ========================================================

    if valid_distance(raw_right):

        right = float(raw_right)

        last_valid_right = right
        invalid_right_count = 0

    else:

        invalid_right_count += 1

        right = last_valid_right


    # ========================================================
    # FOR MANGE FEIL
    # ========================================================

    if (
        invalid_front_count >= MAX_INVALID_READS
        or
        invalid_right_count >= MAX_INVALID_READS
    ):

        return None, None


    # Hvis vi ennå aldri har fått en god måling
    if front is None or right is None:

        return None, None


    # ========================================================
    # LEGG INN I FILTER
    # ========================================================

    front_history.append(front)
    right_history.append(right)


    if len(front_history) > FILTER_SIZE:
        front_history.pop(0)

    if len(right_history) > FILTER_SIZE:
        right_history.pop(0)


    # ========================================================
    # MEDIAN
    # ========================================================

    filtered_front = statistics.median(
        front_history
    )

    filtered_right = statistics.median(
        right_history
    )


    return (
        filtered_front,
        filtered_right
    )


def get_fresh_sensor_reading():

    """
    Brukes etter en sving.

    Vi fjerner gamle data og samler flere
    helt nye målinger.
    """

    reset_sensor_filter()

    front = None
    right = None

    for _ in range(FILTER_SIZE):

        front, right = read_sensors()

        if front is None:
            return None, None

        time.sleep(0.04)


    return front, right


# ============================================================
# SVINGER
# ============================================================

def turn_left_90():

    print("TURN LEFT")

    stop_robot(0.1)

    drive(
        -TURN_SPEED,
        TURN_SPEED,
        TURN_90_TIME
    )

    stop_robot(0.1)

    # Sensoren peker nå i en annen retning.
    reset_sensor_filter()


def turn_right_90():

    print("TURN RIGHT")

    stop_robot(0.1)

    drive(
        TURN_SPEED,
        -TURN_SPEED,
        TURN_90_TIME
    )

    stop_robot(0.1)

    reset_sensor_filter()


# ============================================================
# VEGGFØLGING
# ============================================================

def follow_right_wall(right_distance):

    """
    P-regulator som forsøker å holde
    konstant avstand til høyre vegg.
    """

    error = (
        right_distance
        - TARGET_WALL_DISTANCE
    )

    correction = (
        error
        * WALL_GAIN
    )


    # Ikke tillat ekstrem korreksjon
    correction = limit(
        correction,
        -MAX_CORRECTION,
        MAX_CORRECTION
    )


    left_speed = (
        FORWARD_SPEED
        + correction
    )

    right_speed = (
        FORWARD_SPEED
        - correction
    )


    left_speed = limit(
        left_speed,
        MIN_FORWARD_SPEED,
        MAX_SPEED
    )

    right_speed = limit(
        right_speed,
        MIN_FORWARD_SPEED,
        MAX_SPEED
    )


    motor_serial.send_command(
        left_speed,
        right_speed
    )


# ============================================================
# KJØR INN I KRYSSET
# ============================================================

def advance_into_intersection():

    """
    Robot kjører litt frem før høyresving.

    MEN:

    Den følger frontsensoren mens den kjører.

    Dermed kjører den ikke blindt 0.3 sekunder
    frem dersom en vegg står rett foran.
    """

    start_time = time.time()


    while (
        time.time() - start_time
        < MAX_INTERSECTION_ADVANCE_TIME
    ):

        front, right = read_sensors()


        # Sensorproblem
        if front is None:

            stop_robot()

            return


        # Vegg foran -> ikke kjør videre
        if front <= FRONT_STOP_DISTANCE:

            stop_robot(0.05)

            return


        motor_serial.send_command(
            FORWARD_SPEED,
            FORWARD_SPEED
        )

        time.sleep(LOOP_PERIOD)


    stop_robot(0.05)


# ============================================================
# HÅNDTER HØYRESVING
# ============================================================

def handle_right_turn():

    global right_turn_armed


    print("RIGHT OPENING")


    # Kjør inn mot krysset hvis det er mulig
    advance_into_intersection()


    # Sving høyre
    turn_right_90()


    # Vi har nettopp brukt denne åpningen.
    #
    # Ikke tillat ny høyresving før vi faktisk
    # har funnet en høyrevegg igjen.

    right_turn_armed = False


    # Kjør litt ut av selve svingen.
    drive(
        FORWARD_SPEED,
        FORWARD_SPEED,
        0.15
    )


    reset_sensor_filter()


# ============================================================
# HÅNDTER VEGG FORAN
# ============================================================

def handle_front_wall():

    print("WALL IN FRONT")


    stop_robot(0.15)


    # --------------------------------------------------------
    # FØRST PRØVER VI VENSTRE
    # --------------------------------------------------------

    turn_left_90()


    # Nå må alle målinger være nye fordi sensoren
    # peker i en ny retning.

    front, right = get_fresh_sensor_reading()


    # Sensorproblem
    if front is None:

        print("Sensor error after turn")

        stop_robot()

        return


    # --------------------------------------------------------
    # HVIS VENSTRE OGSÅ ER BLOKKERT
    #
    # Da var dette en blindvei.
    #
    # Vi har allerede snudd 90°.
    # Én ekstra 90° venstresving gir totalt 180°.
    # --------------------------------------------------------

    if front < FRONT_STOP_DISTANCE:

        print("DEAD END")

        turn_left_90()

        get_fresh_sensor_reading()


# ============================================================
# HOVEDPROGRAM
# ============================================================

print("======================================")
print("       MAZE NAVIGATION STARTED")
print("======================================")
print("Ctrl+C to stop")


try:

    while not motor_serial.shutdown_now:

        iteration_start = time.time()


        # ====================================================
        # LES SENSORER
        # ====================================================

        front_distance, right_distance = read_sensors()


        # ====================================================
        # SENSORFEIL
        # ====================================================

        if (
            front_distance is None
            or
            right_distance is None
        ):

            print(
                "SENSOR ERROR -> STOPPING"
            )

            stop_robot(0.2)

            continue


        print(
            "Front:",
            round(front_distance, 1),
            "cm | Right:",
            round(right_distance, 1),
            "cm | Right armed:",
            right_turn_armed
        )


        # ====================================================
        # FINN HØYREVEGGEN IGJEN
        # ====================================================
        #
        # Dette er nøkkelen til å forhindre
        # flere høyresvinger i samme åpne område.

        if (
            not right_turn_armed
            and
            right_distance
            < RIGHT_WALL_FOUND_DISTANCE
        ):

            right_turn_armed = True

            print(
                "RIGHT WALL FOUND -> "
                "RIGHT TURN RE-ARMED"
            )


        # ====================================================
        # 1. HØYRE ÅPEN
        #
        # VIKTIG:
        #
        # Vi krever IKKE lenger at front er åpen.
        #
        # Dermed fungerer:
        #
        # - T-kryss
        # - høyrehjørner
        # ====================================================

        if (
            right_turn_armed
            and
            right_distance
            > RIGHT_OPEN_DISTANCE
        ):

            handle_right_turn()


        # ====================================================
        # 2. VEGG FORAN
        # ====================================================

        elif (
            front_distance
            < FRONT_STOP_DISTANCE
        ):

            handle_front_wall()


        # ====================================================
        # 3. VANLIG KJØRING
        # ====================================================

        else:

            # ------------------------------------------------
            # Hvis høyresving IKKE er armed og siden
            # fortsatt er helt åpen:
            #
            # IKKE bruk wall-following.
            #
            # Ellers ville den store høyreavstanden
            # få roboten til å svinge aggressivt.
            #
            # Kjør i stedet rett frem til vi finner
            # høyreveggen igjen.
            # ------------------------------------------------

            if (
                not right_turn_armed
                and
                right_distance
                > RIGHT_WALL_FOUND_DISTANCE
            ):

                motor_serial.send_command(
                    FORWARD_SPEED,
                    FORWARD_SPEED
                )


            # ------------------------------------------------
            # Vi har en høyrevegg -> følg den
            # ------------------------------------------------

            else:

                follow_right_wall(
                    right_distance
                )


        # ====================================================
        # HOLD CA. 10 Hz
        # ====================================================

        iteration_duration = (
            time.time()
            - iteration_start
        )


        if (
            iteration_duration
            < LOOP_PERIOD
        ):

            time.sleep(
                LOOP_PERIOD
                - iteration_duration
            )


# ============================================================
# CTRL+C
# ============================================================

except KeyboardInterrupt:

    print(
        "\nStopping robot..."
    )


finally:

    # Alltid stopp motorene når programmet avsluttes.

    motor_serial.send_command(
        0,
        0
    )

    print("Goodbye")