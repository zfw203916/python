// package main
// import "fmt"
// var age int
// var level float32 = 1.0
// func main(){
//     //fmt.Printf("%d", age)
//     fmt.Printf("%T", level)
// }
/***
package main
import "fmt"
var level int = 1
var (
    a int
    b string
    c []float32
)

func main(){
    d := 20
    var e int = 40
    //e := 30
    fmt.Printf("a=%d,b=%s,c=%v \n",a,b,c)
    fmt.Println(d)
    fmt.Println(level)
    fmt.Println(e)
}
**/
/**
package main
import (
    "fmt"
    "net"
)
func main(){
    conn, err := net.Dial("tcp","127.0.0.1:8080")
    fmt.Println(conn)
    fmt.Println(err)
}
**/

/**
package main
import "fmt"
func main(){
    var a = 100
    var b = 200
    var c int
    c = b
    b = a
    a = c
    fmt.Printf("a=%d,b=%d", a, b)

}
**/

package main
import "fmt"
func main(){
    var a = 100
    var b = 200
    a,b = b,a
    fmt.Printf("a=%d,b=%d", a, b)
}