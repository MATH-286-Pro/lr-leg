# Hopping practical
from env.leg_gym_env import LegGymEnv
import numpy as np
import matplotlib.pyplot as plt
from practical2_jacobian import jacobian_rel
import tools

if __name__ == "__main__":
    env = LegGymEnv(render=True, 
                    on_rack=False,    # set True to debug 
                    motor_control_mode='TORQUE',
                    action_repeat=1,
                    # record_video=True # 设置录像
                    )

    ### 更改测试时间
    NUM_SECONDS = 5   # simulate N seconds (sim dt is 0.001)
    tau = np.zeros(2) # either torques or motor angles, depending on mode

    # peform one jump, or continuous jumping
    SINGLE_JUMP = True
    SINGLE_JUMP = False

    # sample Cartesian PD gains (can change or optimize)
    # kpCartesian = np.diag([500,300])
    # kdCartesian = np.diag([30,20])
    kpCartesian = np.diag([800,500])
    kdCartesian = np.diag([30,20])

    ### 初始化数据列表用于保存每一步的 foot_pos_err
    foot_value_list = []

    # define variables and force profile
    t = np.linspace(0,NUM_SECONDS,NUM_SECONDS*1000 + 1)
    Fx_max = 60     # max peak force in X direction
    Fz_max = 60     # max peak force in Z direction
    f = 1.8           # frequency

    if SINGLE_JUMP:
        # may want to choose different parameters
        Fx_max = 0     # max peak force in X direction
        Fz_max = 70     # max peak force in Z direction
        f = 2

    # design Z force trajectory as a funtion of Fz_max, f, t
    #   Hint: use a sine function (but don't forget to remove positive forces)
    force_traj_z = Fz_max*np.sin(2*np.pi*f*t)
    force_traj_z[force_traj_z > 0] = 0 ### 保证只有负值

    if SINGLE_JUMP:
        # remove rest of profile (just keep the first peak)
        force_traj_z = Fz_max*np.sin(2*np.pi*f*t)
        # 找到第一个周期的时间范围
        one_period_duration = 1 / f

        # 使用布尔索引保留第一个周期的数据
        force_traj_z[t >= one_period_duration] = 0

    # design X force trajectory as a funtion of Fx_max, f, t
    force_traj_x = Fx_max*np.sin(2*np.pi*f*t)
    force_traj_x[force_traj_x > 0] = 0

    ### 添加测试 (代表组末端相对于组基座的位置，0.0,-0.2 代表组末端在 x=0 z=-0.2 的位置)
    ### 注意范围 (l1=0.209,l2=0.195)
    # sample nominal foot position (can change or optimize)
    nominal_foot_pos = np.array([0.0,-0.2]) 
    # nominal_foot_pos = np.array([0.0,-0.25]) 
    # nominal_foot_pos = np.array([0.195,-0.209]) 正坐着

    # keep track of max z height
    max_base_z = 0

    # Track the profile: what kind of controller will you use? 
    for i in range(NUM_SECONDS*1000):
        # Torques
        tau = np.zeros(2) 

        # Compute jacobian and foot_pos in leg frame (use GetMotorAngles() )
        J, ee_pos_legFrame = jacobian_rel(env.robot.GetMotorAngles())

        # Add Cartesian PD (and/or joint PD? Think carefully about this, and try it out.)
        tau += np.zeros(2) # [TODO]

        foot_pos_error = nominal_foot_pos - ee_pos_legFrame  # 计算差距
        foot_vel = J @ env.robot.GetMotorVelocities()        # 计算微分 = 速度
        desired_force = kpCartesian @ foot_pos_error - kdCartesian @ foot_vel
        tau += J.T @ desired_force

        tau += J.T @ np.array([0,-env.robot.total_mass*9.81]) # 重力补偿

        # Add force profile contribution
        tau += J.T @ np.array([force_traj_x[i], force_traj_z[i]])

        # Apply control, simulate
        env.step(tau)

        # 更新位置列表
        foot_value_list.append(ee_pos_legFrame)

        # Record max base position (and/or other states)
        base_pos = env.robot.GetBasePosition()
        if max_base_z < base_pos[2]:
            max_base_z = base_pos[2]

    print('Peak z', max_base_z)

    # [TODO] make some plots to verify your force profile and system states
    tools.plot(foot_value_list)



