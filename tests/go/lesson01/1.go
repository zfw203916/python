// package main
// import "fmt"

// func main(){
//     name :="World"
//     fmt.Printf("Hello, %s\n",name)
// }

// func main(){
//     var name string
//     var age int
//     name, age = "jack", 20
//     fmt.Printf(name,age)
  
// }
// func main(){
//     // fmt.Print(2<<7-1)
//    for i := 0; i <= 20; i++ {
// 		fmt.Println(i)
// 	}  
// }

// func main(){
//     const length = 5
//     nums := [length]int{10,9,8,7,6,}
//     fmt.Print(nums)
//     fmt.Print(nums[1])
// }

/**
func testPtr(num *int){
    *num  = 20
}
var age int
func main(){
    fmt.Print(age);
}
**/
/*
func sum(a, b int)  int{
    return a + b
}
func main(){
    var a = 100
    var b = 200
    c := sum(a,b)
    fmt.Printf("c=%d", c)
}
*/
/*
package main
import (
    "fmt"
    //"unicode/utf8"
)

func main(){
    s := "码神之路"
    sLength := utf8.RuneCountInString(s)
    fmt.Printf("sLength=%d", sLength)
    
    const(
        Sunday = iota
        Monday
        Tuesday
    )
    fmt.Println(Monday)
    var cat = 1
    var str string = "who am i"
    ptr := &cat
    fmt.Printf("%p,%p \n",&cat, &str)
    fmt.Println(*ptr)
}
*/
/*
package main
import (
    "fmt"
    "flag"
)
func main(){
    
    ptr := new(string)
    *ptr = "码神之路"
    fmt.Printf("%s \n",*ptr) 
    
    mode := flag.String("mode","","运行模式")
    flag.Parse()
    fmt.Printf("运行模式为：%s\n",*mode)
}
*/
/*
package main
import (
    "flag"
    "fmt"
)



func main(){
    name := flag.String("name","世界", "要问好的名字")
    times := flag.Int("times",1,"重复次数")
    loud := flag.Bool("loud", false,"是否大声问好")
    flag.Parse()
    msg := fmt.Sprintf("你好，%s！", *name)
    if *loud {
        msg = msg + "!!!"
    }
    
    // 根据参数输出
    for i := 0; i < *times; i++ {
        fmt.Println(msg)
    }
    
}

*/
/*
package main
import (
    "fmt"
)
func add() int{
    x := 10
    y := 20
    return x + y
}
func div() (int,int){
    return 10, 3
}
func main(){
    result := add()
    fmt.Println(result)
    q, _ := div()
    fmt.Println(q)
}
*/
package main
import "fmt"
func main(){

    // var nums [5]int
    // test := [5]int{1,2,3}
    // fmt.Println("%d, %d\n", nums, test)
    // fmt.Println(cap(test))

    //var array = [4][2]int{{1,2},{3,4},{5,6},{7,8}}
    // array := [4][2]int{1:{10,20},3:{30,40}}
    // var list = []string{}
    // fmt.Println(array)
    // fmt.Println(list)

    // var nums = [...]int{1,2,3,4,5,6,7,8,9,10}
    // mynums := nums[4:6]
    // fmt.Println(mynums)
    //var nums [5]int
    // var nums []int
    // nums = append(nums, 1)
    // fmt.Println(nums)
    // a := []int{1,2,3}
    // b := []int{4,5,6}
    // a = append(a,b...)
    // fmt.Println(a)

    if x := 1; x > 0 {
        fmt.Println("为真进入这里")
    }else{
        fmt.Println("ok")
    }
    fmt.Println("finsh")
}