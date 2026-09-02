import { useEffect, useState } from 'react'
import './index.css'
import { getTasks, createTask, updateTask, deleteTask, type Task } from '../api/tasks'


function Tasks() {
    const [tasks, setTasks] = useState<Task[]>([])
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')

    //   编辑状态
    const [editingId, setEditingId] = useState<number | null>(null)
    const [editTitle, setEditTitle] = useState('')
    const [editDescription, setEditDescription] = useState('')
    const [editStatus, setEditStatus] = useState('pending')
    const [loading, setLoading] = useState(false)

    const getTaskList = async () => {
        try {
            const response = await getTasks()
            setTasks(response.data)
            setLoading(true)
        } catch (error) {
            console.error('获取任务列表失败', error)
        } finally {
            setLoading(false)
        }
    }
    const handleCreateTask = async () => {
        if (!title.trim()) {
            return
        }

        try {
            await createTask({
                title,
                description,
            })

            setTitle('')
            setDescription('')

            await getTaskList()
        } catch (error) {
            console.error(error)
        }
    }

    const handleDeleteTask = async (id: number) => {
        try {
            await deleteTask(id)
            await getTaskList()
        } catch (error) {
            console.error(error)
        }
    }

    const handleEdit = (task: Task) => {
        setEditingId(task.id)
        setEditTitle(task.title)
        setEditDescription(task.description ?? '')
        setEditStatus(task.status)
    }

    const handleCancelEdit = () => {
        setEditingId(null)
    }

    const handleUpdate = async () => {
        if (editingId === null || !editTitle.trim()) {
            return
        }

        try {
            await updateTask(editingId, {
                title: editTitle,
                description: editDescription,
                status: editStatus,
            })

            setEditingId(null)
            await getTaskList()
        } catch (error) {
            console.error(error)
        }
    }

    useEffect(() => {
        getTaskList()
    }, [])

    return (
        <div className="tasks-page">
            <div className="loginout">
                <button onClick={() => {
                    localStorage.removeItem('access_token')
                    window.location.href = '/login'
                }}>
                    退出登录
                </button>
            </div>
            <h1>我的任务</h1>
            <div>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="任务标题"
                />

                <input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="任务描述"
                />

                <button onClick={handleCreateTask}>
                    新建任务
                </button>
            </div>
            {loading ? (
                <div>加载中...</div>
            ) : (
                 <div>
                {tasks.map((task) => (
                    <div key={task.id}>
                        {editingId === task.id ? (
                            <div>
                                <input
                                    value={editTitle}
                                    onChange={(e) => setEditTitle(e.target.value)}
                                />

                                <input
                                    value={editDescription}
                                    onChange={(e) => setEditDescription(e.target.value)}
                                />

                                <select
                                    value={editStatus}
                                    onChange={(e) => setEditStatus(e.target.value)}
                                >
                                    <option value="pending">未完成</option>
                                    <option value="completed">已完成</option>
                                </select>

                                <button onClick={handleUpdate}>
                                    保存
                                </button>

                                <button onClick={handleCancelEdit}>
                                    取消
                                </button>
                            </div>
                        ) : (
                            <div>
                                <h3>任务标题：{task.title}</h3>

                                <p>任务描述：{task.description}</p>

                                <span>状态：{task.status === 'pending' ? '未完成' : '已完成'}</span>

                                <button onClick={() => handleEdit(task)}>
                                    编辑
                                </button>

                                <button onClick={() => handleDeleteTask(task.id)}>
                                    删除
                                </button>
                            </div>
                        )}
                    </div>
                ))}
            </div>
            )}
           
        </div>
    )
}

export default Tasks