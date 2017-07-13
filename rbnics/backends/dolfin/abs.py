# Copyright (C) 2015-2017 by the RBniCS authors
#
# This file is part of RBniCS.
#
# RBniCS is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RBniCS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with RBniCS. If not, see <http://www.gnu.org/licenses/>.
#

from math import fabs, fabs as scalar_fabs
from numpy import ndarray as VectorMatrixType, fabs as vector_matrix_fabs, argmax as vector_matrix_argmax
from numpy.linalg import norm as vector_matrix_norm
from ufl.core.operator import Operator
from dolfin import as_backend_type, Point, vertices
from rbnics.backends.dolfin.matrix import Matrix
from rbnics.backends.dolfin.vector import Vector
from rbnics.backends.dolfin.function import Function
from rbnics.backends.dolfin.wrapping import assert_lagrange_1, function_from_ufl_operators, get_global_dof_coordinates, get_global_dof_component
from rbnics.utils.decorators import backend_for
from rbnics.utils.mpi import parallel_max

# abs function to compute maximum absolute value of an expression, matrix or vector (for EIM). To be used in combination with max
# even though here we actually carry out both the max and the abs!
@backend_for("dolfin", inputs=((Matrix.Type(), Vector.Type(), Function.Type(), Operator), ))
def abs(expression):
    assert isinstance(expression, (Matrix.Type(), Vector.Type(), Function.Type(), Operator))
    if isinstance(expression, Matrix.Type()):
        # Note: PETSc offers a method MatGetRowMaxAbs, but it is not wrapped in petsc4py. We do the same by hand
        mat = as_backend_type(expression).mat()
        row_start, row_end = mat.getOwnershipRange()
        i_max, j_max = None, None
        value_max = None
        for i in range(row_start, row_end):
            cols, vals = mat.getRow(i)
            for (c, v) in zip(cols, vals):
                if value_max is None or fabs(v) > fabs(value_max):
                    i_max = i
                    j_max = c
                    value_max = v
        assert i_max is not None
        assert j_max is not None
        assert value_max is not None
        #
        mpi_comm = mat.comm.tompi4py()
        (global_value_max, global_ij_max) = parallel_max(mpi_comm, value_max, (i_max, j_max), fabs)
        return AbsOutput(global_value_max, global_ij_max)
    elif isinstance(expression, Vector.Type()):
        # Note: PETSc offers VecAbs and VecMax, but for symmetry with the matrix case we do the same by hand
        vec = as_backend_type(expression).vec()
        row_start, row_end = vec.getOwnershipRange()
        i_max = None
        value_max = None
        for i in range(row_start, row_end):
            val = vec.getValue(i)
            if value_max is None or fabs(val) > fabs(value_max):
                i_max = i
                value_max = val
        assert i_max is not None
        assert value_max is not None
        #
        mpi_comm = vec.comm.tompi4py()
        (global_value_max, global_i_max) = parallel_max(mpi_comm, value_max, (i_max, ), fabs)
        return AbsOutput(global_value_max, global_i_max)
    elif isinstance(expression, (Function.Type(), Operator)):
        function = function_from_ufl_operators(expression)
        space = function.function_space()
        assert_lagrange_1(space)
        abs_output = abs(function.vector())
        value_max = abs_output.max_abs_return_value
        global_dof_max = abs_output.max_abs_return_location
        assert len(global_dof_max) == 1
        global_dof_max = global_dof_max[0]
        coordinates_max = get_global_dof_coordinates(global_dof_max, space)
        component_max = get_global_dof_component(global_dof_max, space)
        # Prettify print
        coordinates_max_component_max_dof_max = PrettyTuple(coordinates_max, component_max, global_dof_max)
        return AbsOutput(value_max, coordinates_max_component_max_dof_max)
    else: # impossible to arrive here anyway thanks to the assert
        raise AssertionError("Invalid argument to abs")
    
# Auxiliary class to signal to the max() function that it is dealing with an output of the abs() method
class AbsOutput(object):
    def __init__(self, max_abs_return_value, max_abs_return_location):
        self.max_abs_return_value = max_abs_return_value
        self.max_abs_return_location = max_abs_return_location
        
class PrettyTuple(tuple):
    def __new__(cls, arg0, arg1, arg2):
        return tuple.__new__(cls, (arg0, arg1, arg2))

    def __str__(self):
        output = str(self[0])
        if self[1] >= 0:
            output += " at component " + str(self[1])
        return output
        
        