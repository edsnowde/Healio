'use client'

import Link from "next/link"
import { usePathname } from "next/navigation"

export default function Navbar(){

const pathname=usePathname()

const isKannada=
pathname.startsWith('/kn')


const navLinks=isKannada
? [
{
label:'ಮುಖಪುಟ',
href:'/kn'
},
{
label:'ನೋಂದಣಿ',
href:'/kn/intake'
},
{
label:'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
href:'/kn/dashboard'
}
]
: [
{
label:'Home',
href:'/'
},
{
label:'Intake',
href:'/intake'
},
{
label:'Dashboard',
href:'/dashboard'
}
]



return(

<nav className="
sticky top-0 z-50
bg-white/90
backdrop-blur-xl
border-b
px-8 py-5
">

<div className="
max-w-7xl
mx-auto
flex justify-between items-center
">

{/* Logo */}
<Link
href={isKannada?"/kn":"/"}
className="
text-2xl font-bold
text-emerald-600
"
>
Healio
</Link>



{/* Nav */}
<div className="
flex gap-8
font-medium
">

{
navLinks.map(
(link)=>(
<Link
key={link.href}
href={link.href}
className="
hover:text-emerald-600
transition
"
>
{link.label}
</Link>
))
}

</div>



{/* Language Switch */}
<div className="
border rounded-full
px-4 py-2
flex gap-3
bg-white shadow
">

{
isKannada
?
(
<>
<Link
href="/"
className="
text-gray-500
hover:text-emerald-600
"
>
EN
</Link>

<span className="
font-bold
text-emerald-600
">
ಕನ್ನಡ
</span>
</>
)

:
(
<>
<span className="
font-bold
text-emerald-600
">
EN
</span>

<Link
href="/kn"
className="
text-gray-500
hover:text-emerald-600
"
>
ಕನ್ನಡ
</Link>
</>
)
}

</div>


</div>

</nav>

)

}