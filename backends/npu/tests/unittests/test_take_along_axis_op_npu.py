# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import unittest

import numpy as np
import paddle
from tests.op_test import OpTest, convert_float_to_uint16
from npu_utils import check_soc_version

paddle.enable_static()


class TestTakeAlongAxisOp(OpTest):
    def setUp(self):
        self.set_npu()
        self.init_data()
        self.op_type = "take_along_axis"
        self.xnp = np.random.random(self.x_shape).astype(self.x_type)
        self.target = np.take_along_axis(self.xnp, self.index, self.axis)
        broadcast_shape_list = list(self.x_shape)
        broadcast_shape_list[self.axis] = 1
        self.braodcast_shape = tuple(broadcast_shape_list)
        self.index_broadcast = np.broadcast_to(self.index, self.braodcast_shape)
        self.inputs = {
            "Input": self.xnp,
            "Index": self.index_broadcast,
        }
        self.attrs = {"Axis": self.axis}
        self.outputs = {"Result": self.target}

    def set_npu(self):
        self.__class__.use_custom_device = True
        self.place = paddle.CustomPlace("npu", 0)

    def test_check_output(self):
        self.check_output_with_place(self.place)

    def test_check_grad(self):
        self.check_grad_with_place(self.place, ["Input"], "Result")

    def init_data(self):
        self.x_type = "float32"
        self.x_shape = (5, 5, 5)
        self.index_type = "int32"
        self.index = np.array([[[1]], [[1]], [[2]], [[4]], [[3]]]).astype(
            self.index_type
        )
        self.axis = 2
        self.axis_type = "int64"


class TestCase1(TestTakeAlongAxisOp):
    def init_data(self):
        self.x_type = "float32"
        self.x_shape = (5, 5, 5)
        self.index_type = "int32"
        self.index = np.array([[[0, 1, 2, 1, 4]]]).astype(self.index_type)
        self.axis = 0
        self.axis_type = "int64"


class TestCaseDouble(TestTakeAlongAxisOp):
    def init_data(self):
        self.x_type = "float64"
        self.x_shape = (5, 5, 5)
        self.index_type = "int32"
        self.index = np.array([[[0, 1, 2, 1, 4]]]).astype(self.index_type)
        self.axis = 0
        self.axis_type = "int64"

    def test_check_grad(self):
        self.check_grad_with_place(self.place, ["Input"], "Result")


class TestCaseFloat16(TestTakeAlongAxisOp):
    def init_data(self):
        self.x_type = np.float16
        self.x_shape = (5, 5, 5)
        self.index_type = "int32"
        self.index = np.array([[[0, 1, 2, 1, 4]]]).astype(self.index_type)
        self.axis = 0
        self.axis_type = "int64"


class TestCaseBFloat16(TestTakeAlongAxisOp):
    def setUp(self):
        self.set_npu()
        self.init_data()
        self.op_type = "take_along_axis"
        self.xnp = np.random.random(self.x_shape).astype(np.float32)
        self.target = np.take_along_axis(self.xnp, self.index, self.axis)
        broadcast_shape_list = list(self.x_shape)
        broadcast_shape_list[self.axis] = 1
        self.braodcast_shape = tuple(broadcast_shape_list)
        self.index_broadcast = np.broadcast_to(self.index, self.braodcast_shape)
        self.inputs = {
            "Input": convert_float_to_uint16(self.xnp),
            "Index": self.index_broadcast,
        }
        self.attrs = {"Axis": self.axis}
        self.outputs = {"Result": convert_float_to_uint16(self.target)}

    @check_soc_version
    def test_check_output(self):
        self.check_output_with_place(self.place)

    @check_soc_version
    def test_check_grad(self):
        self.check_grad_with_place(self.place, ["Input"], "Result")

    def init_data(self):
        self.x_type = "bfloat16"
        self.x_shape = (5, 5, 5)
        self.index_type = "int32"
        self.index = np.array([[[0, 1, 2, 1, 4]]]).astype(self.index_type)
        self.axis = 0
        self.axis_type = "int64"


class TestTakeAlongAxisAPI(unittest.TestCase):
    def setUp(self):
        np.random.seed(0)
        self.shape = [3, 3]
        self.index_shape = [1, 3]
        self.index_np = np.array([[0, 1, 2]]).astype("int64")
        self.x_np = np.random.random(self.shape).astype(np.float32)
        self.place = paddle.CustomPlace("npu", 0)
        self.axis = 0

    def test_api_static(self):
        paddle.enable_static()
        with paddle.static.program_guard(paddle.static.Program()):
            x = paddle.static.data("X", self.shape)
            index = paddle.static.data("Index", self.index_shape, "int64")
            out = paddle.take_along_axis(x, index, self.axis)
            exe = paddle.static.Executor(self.place)
            res = exe.run(
                feed={"X": self.x_np, "Index": self.index_np}, fetch_list=[out]
            )
        out_ref = np.array(np.take_along_axis(self.x_np, self.index_np, self.axis))
        for out in res:
            self.assertEqual(np.allclose(out, out_ref, rtol=1e-03), True)

    def test_api_dygraph(self):
        paddle.disable_static(self.place)
        x_tensor = paddle.to_tensor(self.x_np)
        self.index = paddle.to_tensor(self.index_np)
        out = paddle.take_along_axis(x_tensor, self.index, self.axis)
        out_ref = np.array(np.take_along_axis(self.x_np, self.index_np, self.axis))
        self.assertEqual(np.allclose(out.numpy(), out_ref, rtol=1e-03), True)
        paddle.enable_static()


class TestTakeAlongAxisAPICase1(TestTakeAlongAxisAPI):
    def setUp(self):
        np.random.seed(0)
        self.shape = [2, 2]
        self.index_shape = [4, 2]
        self.index_np = np.array([[0, 0], [1, 0], [0, 0], [1, 0]]).astype("int64")
        self.x_np = np.random.random(self.shape).astype(np.float32)
        self.place = paddle.CustomPlace("npu", 0)
        self.axis = 0


if __name__ == "__main__":
    paddle.enable_static()
    unittest.main()
