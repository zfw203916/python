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
package main
import (
    "fmt"
    //"unicode/utf8"
)

func main(){
    /**
    s := "码神之路"
    sLength := utf8.RuneCountInString(s)
    fmt.Printf("sLength=%d", sLength)
    **/
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