
cdef extern from "C.h":

    cdef cppclass C[Y]:
        # wrap-ignore
        # wrap-inherits:
        #     A[Y]
        void Cint(int, Y)
