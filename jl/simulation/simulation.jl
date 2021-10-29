using CPUTime
using YAML



include("environment.jl")
include("plot_using_Plots.jl")

"""シミュレーションのデータ"""
mutable struct Data{T}
    t::StepRangeLen{T}  # 時刻
    q::Vector{Vector{T}}  # ジョイントベクトル
    dq::Vector{Vector{T}}  # ジョイント角速度ベクトル
    ddq::Vector{Vector{T}}  # 制御入力ベクトル
    error::Vector{T}  # eeと目標位置との誤差
    dis_to_obs::Vector{T}
    nodes::Vector{Vector{Vector{Node{T}}}}  # ノード
    goal::Vector{State{T}}
    obs::Vector{Vector{State{T}}}
end




"""
オイラー法でシミュレーション
"""
function euler_method(q₀::Vector{T}, dq₀::Vector{T}, TIME_SPAN::T, Δt::T, obs) where T

    t = range(0.0, TIME_SPAN, step = Δt)  # 時間軸
    #goal = State([0.3, -0.75, 1.0], [0.0, 0.0, 0.0])
    goal = State([0.5, -0.5, 1.3], [0.0, 0.0, 0.0])

    # 初期値
    nodes₀ = update_nodes(nothing, q₀, dq₀)

    data = Data(
        t,
        Vector{Vector{T}}(undef, length(t)),
        Vector{Vector{T}}(undef, length(t)),
        Vector{Vector{T}}(undef, length(t)),
        Vector{T}(undef, length(t)),
        Vector{T}(undef, length(t)),
        Vector{Vector{Vector{Node{T}}}}(undef, length(t)),
        Vector{State{T}}(undef, length(t)),
        Vector{Vector{State{T}}}(undef, length(t))
    )

    data.q[1] = q₀
    data.dq[1] = dq₀
    data.ddq[1] = zeros(T, 7)
    data.error[1] = norm(goal.x - nodes₀[9][1].x)
    data.dis_to_obs[1] = 0.0
    data.nodes[1] = nodes₀
    data.goal[1] = goal
    data.obs[1] = obs
    #println(length(obs))

    # ぐるぐる回す
    for i in 1:length(data.t)-1
        #println("i = ", i)
        data.nodes[i+1] = update_nodes(data.nodes[i], data.q[i], data.dq[i])
        #println("OK3")
        data.error[i+1] = norm(data.goal[i].x .- data.nodes[i][9][1].x)

        data.ddq[i+1], data.dis_to_obs[i+1] = calc_ddq(data.nodes[i], data.goal[i], data.obs[i])
        #ddq[i+1] = zeros(T,7)
        #println("q = ", q[i])
        #println("dq = ", dq[i])
        #println("ddq = ", ddq[i])

        data.q[i+1] = data.q[i] .+ data.dq[i]*Δt
        #q[i+1] = zeros(T,7)
        data.dq[i+1] = data.dq[i] .+ data.ddq[i]*Δt
        data.goal[i+1] = goal
        data.obs[i+1] = obs
    end

    data
end





"""ひとまずシミュレーションやってみｓる"""
function run_simulation(TIME_SPAN::T, Δt::T, obs) where T

    q₀ = q_neutral
    dq₀ = zeros(T, 7)

    data = euler_method(q₀, dq₀, TIME_SPAN, Δt, obs)
    fig = plot_simulation_data(data)
    return data, fig
end





function runner(name)
    params = YAML.load_file(name)
    sim_param = params["sim_param"]
    rmp_param = params["rmp_param"]
    env_param = params["env_param"]
    obs = set_obs(env_param["obstacle"])
    #print(obs)
    data, fig = run_simulation(
        sim_param["TIME_SPAN"], sim_param["TIME_INTERVAL"], obs
    )
    data, fig
end


# using profview
# @profview data, fig = runner("./config/use_RMPfromGDS_test.yaml")

@time data, fig = runner("./config/use_RMPfromGDS_test.yaml")
println("hoge!")
#fig
@time make_animation(data)


# @time t, q, dq, ddq, error, fig, fig2= run_simulation(5.0, 0.01)
# make_animation(q, dq)