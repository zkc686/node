import tensorflow as tf
from node.base import ODESolver


class FixGridODESolver(ODESolver):
    r"""ODE solver with fix grid methods.

    C.f. the slides of Neural ODE in the deep-learning-notes project
    (GitHub @kmkolasinski).

    Args:
        step_fn: Callable[[PhaseVectorField, Time, Time, PhasePoint],
                          PhasePoint]
            Step-function for fixed grid integration method, e.g. Euler's
            method. The last two arguments represents time and time-
            difference respectively.
        num_grids: int

    Returns: ODESolver
    """

    def __init__(self, step_fn, num_grids):
        self.step_fn = step_fn
        self.num_grids = num_grids

    def __call__(self, func, start_time, end_time, initial_value):
        interval = tf.range(start_time, end_time, 1 / self.num_grids)

        def cond(i, phase_point):
            return i < self.num_grids - 1

        def body(i, phase_point):
            time = interval[i]
            time_diff = interval[i + 1] - interval[i]
            next_phase_point = self.step_fn(func, time, time_diff, phase_point)
            return i + 1, next_phase_point

        return tf.while_loop(cond, body, [0, initial_value])


def _apply_to_maybe_list(step_fn_comp):
    """Auxillary decorator XXX

    Args:
        step_fn_comp: Callable[[PhaseVectorField, Time, Time, tf.Tensor],
                               tf.Tensor]

    Returns: Callable[[PhaseVectorField, Time, Time, PhasePoint],
                      PhasePoint]
    """

    def step_fn(f, t, dt, x):
        if not isinstance(x, list):
            return step_fn_comp(f, t, dt, x)
        else:
            return [step_fn_comp(f, t, dt, xi) for xi in x]

    return step_fn


@_apply_to_maybe_list
def euler_step_fn(f, t, dt, x):
    return x + dt * f(x, t)


@_apply_to_maybe_list
def rk2_step_fn(f, t, dt, x):
    k1 = f(x, t)
    k2 = f(x + k1 * dt, t + dt)
    return x + (k1 + k2) / 2 * dt


@_apply_to_maybe_list
def rk4_step_fn(f, t, dt, x):
    k1 = f(x, t)
    k2 = f(x + k1 * dt / 2, t + dt / 2)
    k3 = f(x + k2 * dt / 2, t + dt / 2)
    k4 = f(x + k3 * dt, t + dt)
    return x + (k1 + 2 * k2 + 2 * k3 + k4) / 6 * dt