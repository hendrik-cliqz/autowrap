from smart_ptr cimport shared_ptr
from libcpp.vector cimport vector as libcpp_vector

cdef extern from "test.h":

    cdef cppclass Holder[U]:
        # wrap-instances:
        #   IntHolder := Holder[int]
        #   FloatHolder := Holder[float]
        Holder()
        Holder(U)
        Holder(Holder[U])
        U get()
        void set(U)  # wrap-as:set_

    cdef cppclass Outer[U]:
        # wrap-instances:
        #  B := Outer[int]
        #  C := Outer[float]
        Outer()
        Outer(Outer[U])
        Holder[U] get()
        void set(Holder[U] a)  # wrap-as:set_

        libcpp_vector[Holder].iterator begin() # wrap-iter-begin:__iter__(Holder[U])
        libcpp_vector[Holder].iterator end() # wrap-iter-end:__iter__(Holder[U])

    cdef cppclass SharedPtrTest[U]:
        # wrap-instances:
        #   SharedPtrTestInt := SharedPtrTest[int]
        #   SharedPtrTestFloat := SharedPtrTest[float]
        U sum_values(shared_ptr[Holder[U]] a1, shared_ptr[Holder[U]] a2)
        void set_inner_value(shared_ptr[Holder[U]] & h, U value)



