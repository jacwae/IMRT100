import sys
import time

import imrt_robot_serial
import imrt_xbox


ROBOT_WIDTH = 0.40  # meter
VX_GAIN = 2.0       # maksimal fart framover/bakover
WZ_GAIN = 4.0       # maksimal svinghastighet
DEADZONE = 0.08


def deadzone(value):
    """Fjerner små bevegelser rundt midtpunktet på styrespaken."""
    if abs(value) < DEADZONE:
        return 0.0
    return value


def get_trigger(controller, side):
    """
    Henter triggerverdien. Flere metodenavn støttes fordi ulike
    versjoner av imrt_xbox kan bruke forskjellige navn.
    """
    if side == "left":
        method_names = (
            "get_left_trigger",
            "get_l2",
            "get_lt",
            "get_trigger_left",
        )
    else:
        method_names = (
            "get_right_trigger",
            "get_r2",
            "get_rt",
            "get_trigger_right",
        )

    for method_name in method_names:
        method = getattr(controller, method_name, None)

        if callable(method):
            return float(method())

    raise AttributeError(
        f"Fant ingen metode for {side} trigger i imrt_xbox."
    )


def normalize_trigger(value, uses_minus_one_range):
    """
    Gjør triggerverdien om til området 0–1.

    Støtter både:
      -1 til 1
       0 til 1
       0 til 255
    """
    if uses_minus_one_range:
        value = (value + 1.0) / 2.0
    elif value > 1.0:
        value = value / 255.0

    return max(0.0, min(1.0, value))


def main():
    controller = imrt_xbox.IMRTxbox()
    motor_serial = imrt_robot_serial.IMRTRobotSerial()

    # Koble til roboten
    try:
        motor_serial.connect("/dev/ttyACM0")
    except Exception as error:
        print("Kunne ikke åpne porten.")
        print("Er roboten koblet til?")
        print(f"Feilmelding: {error}")
        controller.shutdown()
        sys.exit(1)

    # Start mottak av data fra roboten
    motor_serial.run()

    try:
        # Les triggerne i hvilestilling for å finne verdiområdet
        left_trigger_neutral = get_trigger(controller, "left")
        right_trigger_neutral = get_trigger(controller, "right")

        left_uses_minus_one = left_trigger_neutral < -0.5
        right_uses_minus_one = right_trigger_neutral < -0.5

        while not motor_serial.shutdown_now:
            # Venstre styrespak styrer venstre og høyre
            steering = deadzone(controller.get_left_x())

            # L2 kjører bakover og R2 kjører framover
            raw_l2 = get_trigger(controller, "left")
            raw_r2 = get_trigger(controller, "right")

            l2 = normalize_trigger(
                raw_l2,
                left_uses_minus_one
            )

            r2 = normalize_trigger(
                raw_r2,
                right_uses_minus_one
            )

            # R2 gir positiv fart, L2 gir negativ fart
            throttle = r2 - l2

            # Beregn lineær fart og rotasjon
            vx = VX_GAIN * throttle
            wz = -WZ_GAIN * steering

            # Beregn hastigheten til venstre og høyre motor
            v1 = (vx - ROBOT_WIDTH * wz / 2.0) * 200
            v2 = (vx + ROBOT_WIDTH * wz / 2.0) * 200

            print(
                f"L2: {l2:.2f}  "
                f"R2: {r2:.2f}  "
                f"styring: {steering:+.2f}  "
                f"motorer: {int(v1)}, {int(v2)}",
                end="\r"
            )

            motor_serial.send_command(int(v1), int(v2))
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nAvsluttet av brukeren")

    finally:
        # Stopp roboten før programmet avsluttes
        try:
            motor_serial.send_command(0, 0)
        except Exception:
            pass

        controller.shutdown()
        print("\nRobot stoppet. Avslutter programmet.")


if __name__ == "__main__":
    main()