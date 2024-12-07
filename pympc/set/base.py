import numpy as np
import cvxpy as cp
import matplotlib.pyplot as plt
import abc
from .exception import *


class SetBase(metaclass=abc.ABCMeta):
    # 集合的维度
    @property
    @abc.abstractmethod
    def n_dim(self) -> int:
        ...

    # 判断是否为内点，同时也可以作为cvxpy求解器接口
    @abc.abstractmethod
    def contains(self, point: np.ndarray or cp.Expression) -> bool or cp.Constraint:
        ...

    # 判断一个集合是否被包含于另一个集合
    @abc.abstractmethod
    def subset_eq(self, other: 'SetBase'):
        ...

    # 画图（仅实现二维画图）
    @abc.abstractmethod
    def plot(self, ax: plt.Axes, n_points=2000, color='b') -> None:
        ...

    # 闵可夫斯基和（或平移）
    @abc.abstractmethod
    def __add__(self, other: 'SetBase' or np.ndarray) -> 'SetBase':
        ...

    # 庞特里亚金差，即闵可夫斯基和的逆运算
    # 即若 p2 = p1 + p3，则 p3 = p2 - p1，只有当输入为一个点（数组）时该运算等价于 (-p1) + p2
    @abc.abstractmethod
    def __sub__(self, other: 'SetBase' or np.ndarray) -> 'SetBase':
        ...

    # 多面体坐标变换，Set_new = Set @ mat 意味着 Set 是将 Set_new 中的所有点通过 mat 映射后的区域，这一定义是为了方便计算不变集
    @abc.abstractmethod
    def __matmul__(self, other: np.ndarray) -> 'SetBase':
        ...

    # 多面体坐标变换，Set_new = Set @ mat 意味着 Set_new 是将 Poly 中的所有点通过 mat 映射后的区域，这一定义是为了方便计算不变集
    @abc.abstractmethod
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs) -> 'SetBase' or NotImplemented:
        ...

    # 集合的放缩
    @abc.abstractmethod
    def __mul__(self, other: int or float) -> 'SetBase':
        ...

    def __rmul__(self, other: int or float) -> 'SetBase':
        return self.__mul__(other)

    def __truediv__(self, other: int or float) -> 'SetBase':
        return self.__mul__(1 / other)

    # 集合取交集
    @abc.abstractmethod
    def __and__(self, other: 'SetBase') -> 'SetBase':
        ...

    # 判断两个集合是否相等
    @abc.abstractmethod
    def __eq__(self, other: 'SetBase') -> bool:
        ...


def support_fun(eta: np.ndarray, s: SetBase) -> int or float:
    if eta.ndim != 1:
        raise SetTypeException('input \'eta\'', 'support function', '1D array')
    if eta.size != s.n_dim:
        raise SetDimensionException('\'eta\'', '\'polyhedron\'')

    var = cp.Variable(s.n_dim)
    prob = cp.Problem(cp.Maximize(eta @ var), [s.contains(var)])
    prob.solve(solver=cp.GLPK)

    return prob.value
