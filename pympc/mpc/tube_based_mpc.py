import numpy as np
import cvxpy as cp
from functools import cache
from .base import MPCBase
from ..set import Polyhedron, support_fun, unit_cube
from .exception import *


class TubeBasedMPC(MPCBase):
    def __init__(self, a: np.ndarray, b: np.ndarray, q: np.ndarray, r: np.ndarray, pred_horizon: int,
                 state_set: Polyhedron, input_set: Polyhedron, noise_set: Polyhedron,
                 terminal_set_type='polyhedron', solver=cp.PIQP):
        super().__init__(a, b, q, r, pred_horizon, terminal_set_type, solver)

        if not (self.state_dim == noise_set.n_dim):
            raise MPCDimensionException('noise set and state in controller!')

        self.__noise_set = noise_set

        self.__tightened_state_set = state_set - self.disturbance_invariant_set
        self.__tightened_input_set = input_set - self.k @ self.disturbance_invariant_set

    def __call__(self, real_time_state: np.ndarray) -> np.ndarray:
        self.real_time_state = real_time_state
        self.problem.solve(solver=self.solver)

        return self.input_ini.value - self.k @ (real_time_state - self.state_ini.value)

    @property
    def noise_set(self) -> Polyhedron:
        return self.__noise_set

    @property
    def state_set(self) -> Polyhedron:
        return self.__tightened_state_set

    @property
    def input_set(self) -> Polyhedron:
        return self.__tightened_input_set

    @property
    def initial_constraint(self) -> cp.Constraint:
        return self.disturbance_invariant_set.contains(self.real_time_state - self.state_ini)

    @property
    @cache
    def disturbance_invariant_set(self, alpha=0.2, epsilon=0.001) -> Polyhedron:
        alp = alpha

        # 由于多次给集合左乘 A_k，且 A_k 可逆，可以提前求好 A_k 的逆并在下面的 计算 1、计算 2 中右乘 A_k 的逆，这里为了方便理解，没有这么做
        # a_k_inv = npl.inv(self.a - self.b @ self.k)
        a_k = self.a - self.b @ self.k

        a_k_s = np.eye(self.state_dim)
        a_k_s_noise_set = self.__noise_set
        sum_a_k_s_noise_set = self.__noise_set
        alpha_noise_set = alp * self.__noise_set

        while True:
            if a_k_s_noise_set.subset_eq(alpha_noise_set):
                break

            a_k_s = a_k @ a_k_s

            # 计算 1 - - - - - - - - - - - - - - - - - - - #
            # a_k_s_noise_set = a_k_s_noise_set @ a_k_inv
            a_k_s_noise_set = a_k @ a_k_s_noise_set
            # - - - - - - - - - - - - - - - - - - - - - - #

            sum_a_k_s_noise_set = sum_a_k_s_noise_set + a_k_s_noise_set

        alp = max([support_fun(self.__noise_set.l_mat[i, :], a_k_s_noise_set) / a_k_s_noise_set.r_vec[i]
                   for i in range(self.__noise_set.n_edges)])

        f_alpha_s_set = sum_a_k_s_noise_set / (1 - alp)

        a_k_n = a_k_s
        a_k_n_noise_set = a_k_s_noise_set
        sum_a_k_n_noise_set = sum_a_k_s_noise_set
        # 这里用一个单位球的内接超正方体代替单位球
        unit_cube_ = unit_cube(self.state_dim, 2 * epsilon / np.sqrt(self.state_dim))

        while True:
            a_k_n = a_k @ a_k_n

            if a_k_n_noise_set.subset_eq(unit_cube_):
                break

            # 计算 2 - - - - - - - - - - - - - - - - - - - #
            # a_k_n_noise_set = a_k_n_noise_set @ a_k_inv
            a_k_n_noise_set = a_k @ a_k_n_noise_set
            # - - - - - - - - - - - - - - - - - - - - - - #

            sum_a_k_n_noise_set = sum_a_k_n_noise_set + a_k_n_noise_set

        disturbance_invariant_set = a_k_n @ f_alpha_s_set + sum_a_k_n_noise_set

        return disturbance_invariant_set
