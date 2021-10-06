"""RMPシミュレーション"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anm
import scipy.integrate as integrate


import time


from new import BaxterRobotArmKinematics
from rmp import OriginalRMP


class PositinData:
    def __init__(self,):
        self.x = []
        self.y = []
        self.z = []
    
    def add(self, X):
        self.x.append(X[0, 0])
        self.y.append(X[1, 0])
        self.z.append(X[2, 0])


class FrameData:
    def __init__(self, arm):
        self._get_joint_position(arm)
        self._get_cpoints_position(arm)
    
    
    def _get_joint_position(self, arm):
        self.joint_positions = PositinData()
        for o in arm.get_joint_positions():
            self.joint_positions.add(o)
        return
    
    
    def _get_cpoints_position(self, arm):
        self.cpoints_potisions = []
        for cpoints in arm.cpoints_x:
            _cs = PositinData()
            for c in cpoints:
                _cs.add(c)
            self.cpoints_potisions.append(_cs)
        return



class SimulationData:
    
    def __init__(self,):
        self.data = []
        self.ee = PositinData()
        pass
    
    
    def add_data(self, arm):
        self.data.append(FrameData(arm))
        
        self.ee.add(arm.Ts_Wo[-1].o)
        return



class Simulator:
    """"""
    
    def __init__(self, TIME_SPAN=5, TIME_INTERVAL=0.01):
        self.TIME_SPAN = TIME_SPAN
        self.TIME_INTERVAL = TIME_INTERVAL
        
        return
    
    
    def run_simulation(self,):
        
        
        self.gl_goal = np.array([[0.3, -0.6, 1]]).T
        self.obs = np.array([[0.8, -0.6, 1]]).T
        dobs = np.zeros((3, 1))
        
        
        t = np.arange(0.0, self.TIME_SPAN, self.TIME_INTERVAL)
        
        arm = BaxterRobotArmKinematics(isLeft=True)
        rmp = OriginalRMP(
            attract_max_speed = 2, 
            attract_gain = 10, 
            attract_a_damp_r = 0.3,
            attract_sigma_W = 1, 
            attract_sigma_H = 1, 
            attract_A_damp_r = 0.3, 
            obs_scale_rep = 0.2,
            obs_scale_damp = 1,
            obs_ratio = 0.5,
            obs_rep_gain = 0.5,
            obs_r = 15,
            jl_gamma_p = 0.05,
            jl_gamma_d = 0.1,
            jl_lambda = 0.7,
            joint_limit_upper = arm.q_max,
            joint_limit_lower = arm.q_min,
        )
        
        
        self.data = SimulationData()
        
        
        def _eom(t, state):
            
            q = np.array([state[0:7]]).T
            dq = np.array([state[7:14]]).T
            
            arm.update_all(q, dq)  # ロボットアームの全情報更新
            
            pulled_f_all = []
            pulled_M_all = []
            
            for i in range(8):
                for x, dx, J in zip(arm.cpoints_x[i], arm.cpoints_dx[i], arm.Jos_cpoints[i]):
                    a = rmp.a_obs(x, dx, self.obs)
                    M = rmp.metric_obs(x, dx, self.obs, a)
                    f = M @ a
                    
                    _pulled_f = J.T @ f
                    _pulled_M = J.T @ M @ J
                    
                    pulled_f_all.append(_pulled_f)
                    pulled_M_all.append(_pulled_M)

                    if i == 7:
                        a = rmp.a_attract(x, dx, self.gl_goal)
                        M = rmp.metric_attract(x, dx, self.gl_goal, a)
                        f = M @ a
                        
                        _pulled_f = J.T @ f
                        _pulled_M = J.T @ M @ J
                        
                        pulled_f_all.append(_pulled_f)
                        pulled_M_all.append(_pulled_M)
            
            
            a_jl = rmp.a_joint_limit(q, dq)
            M_jl = rmp.metric_joint_limit(q)
            f_jl = M_jl @ a_jl
            
            pulled_f_all = np.sum(pulled_f_all, axis=0) + f_jl
            pulled_M_all = np.sum(pulled_M_all, axis=0) + M_jl
            
            ddq = np.linalg.pinv(pulled_M_all) @ pulled_f_all
            
            dstate = np.concatenate([dq, ddq], axis=0)
            dstate = np.ravel(dstate).tolist()
            
            
            
            # 以下 視覚化のためのデータ保存
            
            self.data.add_data(arm)
            
            
            return dstate
        
        
        print("シミュレーション実行中...")
        start = time.time()
        self.sol = integrate.solve_ivp(
            fun=_eom,
            t_span=(0.0, self.TIME_SPAN),
            y0=np.ravel(np.concatenate([arm.q, arm.dq])).tolist(),
            method='RK45',
            t_eval=t,
        )
        print("シミュレーション実行終了")
        print("実行時間 = ", time.time() - start)

        return


    def plot(self,):
        
        # fig = plt.figure()
        # ax = fig.add_subplot()
        # for i in range(7):
        #     ax.plot(sol.t, sol.y[i], label=str(i+1))
        # ax.legend()
        # ax.grid(True)
        # ax.set_xlabel('time')
        # ax.set_ylabel('joint angle')
        
        
        # arm = BaxterRobotArmKinematics(isLeft=True)
        # origins_his = []
        # for i in range(len(sol.t)):
        #     _q = [sol.y[j][i] for j in range(7)]
        #     q = np.array([_q]).T
        #     arm.update_all(q, arm.dq)
            
        #     _os = arm.get_joint_positions()
        #     os = [i, 0, 0, 0]
        #     for o in _os:
        #         os.extend(np.ravel(o).tolist())
        #     origins_his.append(os)
        
        
        # origins_his_T = [list(x) for x in zip(*origins_his)]
        
        
        
        # アニメーション
        fig_ani = plt.figure()
        ax = fig_ani.add_subplot(projection = '3d')
        ax.grid(True)
        ax.set_xlabel('X[m]')
        ax.set_ylabel('Y[m]')
        ax.set_zlabel('Z[m]')

        # ## 三軸のスケールを揃える
        # # 使用するデータを指定
        # list_x = []  # x軸配列
        # list_y = []  # y軸配列
        # list_z = []  # z軸配列
        # for i in range(0, 11, 1):
        #     list_x.extend(origins_his_T[1 + 3 * i][1:])
        #     list_y.extend(origins_his_T[2 + 3 * i][1:])
        #     list_z.extend(origins_his_T[3 + 3 * i][1:])
        # # 軸をセット
        # max_range = np.array([
        #     max(list_x) - min(list_x),
        #     max(list_y) - min(list_y),
        #     max(list_z) - min(list_z)
        #     ]).max() * 0.5
        # mid_x = (max(list_x) + min(list_x)) * 0.5
        # mid_y = (max(list_y) + min(list_y)) * 0.5
        # mid_z = (max(list_z) + min(list_z)) * 0.5
        # ax.set_xlim(mid_x - max_range, mid_x + max_range)
        # ax.set_ylim(mid_y - max_range, mid_y + max_range)
        # ax.set_zlim(mid_z - max_range, mid_z + max_range)




        # 目標点
        ax.scatter(
            self.gl_goal[0, 0], self.gl_goal[1, 0], self.gl_goal[2, 0],
            s = 100, label = 'goal point', marker = '*', color = '#ff7f00', 
            alpha = 1, linewidths = 1.5, edgecolors = 'red')
        ax.scatter(
            self.obs[0, 0], self.obs[1, 0], self.obs[2, 0],
            s = 100, label = 'obstacle point', marker = '+', color = 'k', 
            alpha = 1)


        # 初期値
        d = self.data.data[0]

        # アーム全体
        bodys = []
        bodys.append(
            ax.plot(
                d.joint_positions.x, d.joint_positions.y, d.joint_positions.z,
                "o-", color = "blue"
            )[0]
        )

        # グリッパー（エンドエフェクター）軌跡
        gl = []
        gl.append(
            ax.plot(
            self.data.ee.x[0], self.data.ee.y[0], self.data.ee.z[0],
            "-", label = "gl", color = "#ff7f00"
            )[0]
        )

        #ax.legend()

        # 時刻表示
        timeani = [ax.text(0.8, 0.2, 0.01, "time = 0.0 [s]", size = 10)]
        time_template = 'time = %s [s]'

        # # 結果表示
        # ax.text(0.8, 0.3, 0.01, result[0], color = "r", size = 14)

        ax.set_box_aspect((1,1,1))

        def update(i):
            """アニメーションの関数"""
            i = i + 1
            
            d = self.data.data[i]
            
            body_x, body_y, body_z = [], [], []
            for j in range(0, 11, 1):
                # body用の配列作成
                body_x.append(d.joint_positions.x)
                body_y.append(d.joint_positions.y)
                body_z.append(d.joint_positions.z)
            
            item1 = bodys.pop(0)
            ax.lines.remove(item1)
            bodys.append(ax.plot(body_x, body_y, body_z, "o-", color = "blue")[0])
            
            item2 = gl.pop(0)
            ax.lines.remove(item2)
            gl.append(ax.plot(
                self.data.ee.x[1:i], 
                self.data.ee.y[1:i], 
                self.data.ee.z[1:i], "-", color = "#ff7f00")[0])
            
            # 時刻表示
            timeani.pop().remove()
            timeani_, = [ax.text(0.8, 0.12, 0.01, time_template % (i * self.TIME_INTERVAL), size = 10)]
            timeani.append(timeani_)
            return None

        ani = anm.FuncAnimation(
            fig = fig_ani, 
            func = update, 
            frames = int(self.TIME_SPAN / self.TIME_INTERVAL),
            interval = self.TIME_INTERVAL * 0.001)

        plt.show()




def main():
    simu = Simulator()
    simu.run_simulation()
    simu.plot()



if __name__ == "__main__":
    main()