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

from rbnics.utils.decorators import PreserveClassName, ReducedProblemDecoratorFor
from .online_stabilization import OnlineStabilization

@ReducedProblemDecoratorFor(OnlineStabilization)
def OnlineStabilizationDecoratedReducedProblem(EllipticCoerciveReducedProblem_DerivedClass):
    
    @PreserveClassName
    class OnlineStabilizationDecoratedReducedProblem_Class(EllipticCoerciveReducedProblem_DerivedClass):
    
        def _solve(self, N, **kwargs):
            # Temporarily change value of stabilized attribute in truth problem
            bak_stabilized = self.truth_problem.stabilized
            self.truth_problem.stabilized = kwargs.get("online_stabilization", True)
            EllipticCoerciveReducedProblem_DerivedClass._solve(self, N, **kwargs)
            self.truth_problem.stabilized = bak_stabilized
    
    # return value (a class) for the decorator
    return OnlineStabilizationDecoratedReducedProblem_Class