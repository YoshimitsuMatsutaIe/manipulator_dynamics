

# """
# rmp-treeで所望の加速度を計算
# """
# module RMPTree


# export update_nodes
# export calc_desired_ddq



using LinearAlgebra



include("../utils.jl")

include("./rmp.jl")
include("../kinematics/kinematics.jl")


# using .Kinematics
# using .RMP
# using .Utilis



#attractor = OriginalRMPAttractor(2.0, 10.0, 0.15, 1.0, 1.0, 5.0)
#const obs_avoidance = OriginalRMPCollisionAvoidance(0.2, 1.0, 0.5, 0.5, 1.0)



"""所望の加速度を計算（resolve演算結果を返す）"""
function calc_desired_ddq(
    nodes::Vector{Vector{Node{T}}},
    rmp_param::NamedTuple,#{Union{OriginalRMPAttractor{T}, RMPfromGDSAttractor{T}}, Union{OriginalRMPCollisionAvoidance{T}, RMPfromGDSCollisionAvoidance{T}}, Vector{OriginalJointLimitAvoidance{T}}},
    goal::State{T},
    obs::Vector{State{T}}
) where T

    #root_f = Vector{T}(undef, 7)
    #root_M = Matrix{T}(undef, 7, 7)
    root_f = zeros(T, 7)
    root_M = zeros(T, 7, 7)

    dis_to_obs = 0.0

    for i in 1:9
        if i == 1
            _f, _M = get_natural(
                rmp_param.joint_limit_avoidance, nodes[i][1].x, nodes[i][1].dx, q_max, q_min
            )
            root_f += _f
            root_M += _M
        elseif i == 9
            _f, _M = get_natural(
                rmp_param.attractor, nodes[i][1].x, nodes[i][1].dx, goal.x
            )
            _pulled_f, _pulled_M = pullbacked_rmp(_f, _M, nodes[i][1].Jo,)
            @. root_f += _pulled_f
            @. root_M += _pulled_M


        else
            for j in 1:length(nodes[i])
                _temp_dis_to_obs = Vector{T}(undef, length(obs))
                for k in 1:length(obs)
                    _temp_dis_to_obs[k] = norm(obs[k].x .- nodes[i][j].x)
                    _f, _M = get_natural(
                        rmp_param.obs_avoidance[i], nodes[i][j].x, nodes[i][j].dx, obs[k].x
                    )
                    _pulled_f, _pulled_M = pullbacked_rmp(_f, _M, nodes[i][j].Jo,)
                    @. root_f += _pulled_f
                    @. root_M += _pulled_M
                end
                _d = minimum(_temp_dis_to_obs)
                if dis_to_obs < _d
                    dis_to_obs = _d
                end
            end
        end
    end

    #root_f += zeros(T, 7)
    #root_M += zeros(T, 7, 7)

    #println("root_f = ", root_f)
    #println("root_M = ", root_M)


    ddq = pinv(root_M) * root_f
    #println("ddq = ", ddq)
    #ddq = np.linalg.pinv(root_M) * root_f

    #ddq = zeros(T, 7)
    return ddq, dis_to_obs
end


"""nodeを更新"""
function update_nodes(nodes::Vector{Vector{Node{T}}}, q::Vector{T}, dq::Vector{T}) where T
    # 更新
    _, _,
    _, _, _, _,
    _, Jos_cpoint_all,
    cpoints_x_global, cpoints_dx_global,
    _, _, = calc_all(q, dq)
    for i in 1:9
        #println("sinu")
        #println(nodes[2])
        for j in 1:length(nodes[i])
            #println("???")
            if i == 1
                nodes[i][j].x = q
                nodes[i][j].dx = dq
            else
                nodes[i][j].x = cpoints_x_global[i-1][j]
                nodes[i][j].dx = cpoints_dx_global[i-1][j]
                nodes[i][j].Jo = Jos_cpoint_all[i-1][j]
            end
        end
    end
    #println("hh")
    return nodes
end


"""nodeを新規作成"""
function update_nodes(nodes::Nothing, q::Vector{T}, dq::Vector{T}) where T
    # 更新
    _, _,
    _, _, _, _,
    _, Jos_cpoint_all,
    cpoints_x_global, cpoints_dx_global,
    _, _, = calc_all(q, dq)
    nodes = Vector{Vector{Node{T}}}(undef, 9)
    for i in 1:9
        #println("i = ", i)
        if i == 1
            _children_node = Vector{Node{T}}(undef, 1)
            _children_node[1] = Node(q, dq, Matrix{T}(I, 7, 7))
            #println("wow")
        else
            n = length(cpoints_local[i-1])
            _children_node = Vector{Node{T}}(undef, n)
            for j in 1:n
                _children_node[j] = Node(
                    cpoints_x_global[i-1][j],
                    cpoints_dx_global[i-1][j],
                    Jos_cpoint_all[i-1][j]
                )
            end
        end
        nodes[i] = _children_node
    end
    return nodes
end



#end