package main
import (
    "encoding/json"
    "flag"
    "fmt"
    "os"
)

// ---------- 1. 数据结构 ----------

// Todo一条待办
type Todo struct {
    ID int `json:"id"`
    Text string `json:"text"`
    Done bool `json:"done"`
}

// ---------- 2. 存取 ----------
const file ="todo.json"

// load 从文件读取所有待办
func load() []Todo {
    data, err := os.ReadFile(file)
    if err != nil {
        return []Todo{} // 文件不存在，返回空列表
    }
    var todos []Todo
    json.Unmarshal(data, &todos)
    return todos
}

// save 把待办写回文件
func save(todos []Todo){
    data, _ := json.MarshalIndent(todos, "", "  ")
    os.WriteFile(file, data, 0644)
}

// ---------- 3. 主逻辑 ----------
func main(){
    // 解析命令行：第一个参数是动作，第二个是内容
    flag.Parse()
    args := flag.Args()
    if len(args) == 0 {
        fmt.Println("用法: todo [add|list|done|del] [内容]")
        return
    }
    todos := load()
    action := args[0]

    switch action {
        case "add":
            if len(args) < 2 {
                fmt.Println("请提供内容，例如: todo add 学习Go")
                return 
            }
            id := 1
            if len(todos) > 0{
                id = todos[len(todos) - 1].ID + 1 // 简单自增 ID
            }
            todos = append(todos, Todo{ID:id, Text:args[1], Done: false})
            save(todos)
            fmt.Println("已添加:", args[1])
        case "list":
            if len(args) == 0{
                fmt.Println("暂无待办")
                return
            }
            for _, t := range todos{
                status := " "
                if t.Done{
                    status = "✔"
                }
                fmt.Printf("[%s] %d. %s\n", status, t.ID, t.Text)
            }
        
        case "done":
            if len(args) < 2 {
                fmt.Println("请提供 ID，例如: todo done 1")
                return 
            }

            var id int
            fmt.Sscanf(args[1], "%d",  &id)
            for i := range todos {
                if todos[i].ID == id {
                    todos[i].Done = true
                }
            }
            save(todos)
            fmt.Println("已完成:", id)
        
        case "del":
            if len(args) < 2 {
                fmt.Println("请提供 ID，例如: todo del 1")
                return
            }
            var id int
            fmt.Sscanf(args[1], "%d", &id)
            var result []Todo
            for _, t := range todos {
                if t.ID != id {
                    result = append(result, t)
                }
            }
            save(result)
            fmt.Println("已删除:", id)
        default:
            fmt.Println("未知命令:", action)
    }
}