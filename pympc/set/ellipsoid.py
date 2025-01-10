import numpy as np
import numpy.linalg as npl
import cvxpy as cp
import matplotlib.pyplot as plt
from typing import Union
from .base import SetBase
from .exception import *


class Ellipsoid(SetBase):
    def __init__(self, p: np.ndarray, alpha: Union[int, float], center: np.ndarray = None):
        try:
            _ = npl.cholesky(p)
        except npl.LinAlgError:
            raise SetTypeException("'P' matrix", "ellipsoid", "positive definite matrix")

        self.__p = p
        self.__n_dim = p.shape[0]
        self.__alpha = alpha

        self.__center = np.zeros(self.__n_dim) if center is None else center

    def __str__(self) -> str:
        return (
            "====================================================================================================\n"
            "(x - center).T @ p @ (x - center) <= alpha\n"
            "====================================================================================================\n"
            f"p:\n"
            f"{self.__p}\n"
            "----------------------------------------------------------------------------------------------------\n"
            f"alpha:\n"
            f"{self.__alpha}\n"
            "----------------------------------------------------------------------------------------------------\n"
            f"center:\n"
            f"{self.__center}\n"
            "===================================================================================================="
        )

    def contains(self, point: Union[np.ndarray, cp.Expression]) -> Union[bool, cp.Constraint]:
        if isinstance(point, np.ndarray):
            res = np.all((point - self.__center) @ self.__p @ (point - self.__center) - self.__alpha <= 0)
        else:
            res = cp.quad_form(point - self.__center, self.__p) - self.__alpha <= 0

        return res

    def subset_eq(self, other: "Ellipsoid") -> bool:
        raise SetNotImplementedException("subset_eq", "ellipsoid")

    def plot(self, ax: plt.Axes, n_points=2000, color="b") -> None:
        if self.__n_dim != 2:
            raise SetPlotException()

        axis_max = np.sqrt(self.__alpha / npl.eigvals(self.__p))
        x_max, y_max = axis_max * 1.5
        x_min, y_min = -axis_max * 1.5

        x = np.linspace(x_min, x_max, n_points)
        y = np.linspace(y_min, y_max, n_points)
        x_grid, y_grid = np.meshgrid(x, y)
        x_grid = x_grid - self.__center[0]
        y_grid = y_grid - self.__center[1]

        z = (
            x_grid**2 * self.__p[0, 0]
            + x_grid * y_grid * (self.__p[0, 1] + self.__p[1, 0])
            + y_grid**2 * self.__p[1, 1]
        )

        ax.contour(x_grid, y_grid, z, levels=[self.__alpha], colors=color)

    @property
    def p(self) -> np.ndarray:
        return self.__p

    @property
    def n_dim(self) -> int:
        return self.__n_dim

    @property
    def alpha(self) -> Union[int, float]:
        return self.__alpha

    @property
    def center(self) -> np.ndarray:
        return self.__center

    def __add__(self, other: Union["Ellipsoid", np.ndarray]) -> "Ellipsoid":
        if isinstance(other, Ellipsoid):
            raise SetNotImplementedException("pontryagin difference", "ellipsoid")
        else:
            return self.__class__(self.__p, self.__alpha, self.__center + other)

    def __sub__(self, other: Union["Ellipsoid", np.ndarray]) -> "Ellipsoid":
        if isinstance(other, Ellipsoid):
            raise SetNotImplementedException("pontryagin difference", "ellipsoid")
        else:
            return self.__add__(-other)

    def __matmul__(self, other: np.ndarray) -> "Ellipsoid":
        if other.ndim != 2:
            raise SetCalculationException("ellipsoid", "multiplied", "2D array")
        if other.shape[0] != self.__n_dim:
            raise SetCalculationException("ellipsoid", "multiplied", "array with matching dimension")

        return self.__class__(other.T @ self.__p @ other, self.__alpha, self.__center)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs) -> "Ellipsoid":
        if ufunc == np.matmul:
            lhs, rhs = inputs
            try:
                res = self.__matmul__(npl.inv(lhs))
            except npl.LinAlgError:
                res = NotImplemented
        elif ufunc == np.add:
            lhs, rhs = inputs
            res = self.__add__(lhs)
        else:
            res = NotImplemented

        return res

    # 多面体的放缩
    def __mul__(self, other: Union[int, float]) -> "Ellipsoid":
        if other < 0:
            raise SetCalculationException("ellipsoid", "multiplied", "positive number")

        return self.__class__(self.__p, self.__alpha * other, self.__center)

    def __and__(self, other: "Ellipsoid") -> "Ellipsoid":
        raise SetNotImplementedException("intersection", "ellipsoid")

    def __eq__(self, other: "Ellipsoid") -> bool:
        return (self.__center == other.__center) and np.all((self.__p / other.__p) == (self.__alpha / other.__alpha))
