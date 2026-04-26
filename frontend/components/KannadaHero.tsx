import {
ArrowRight,
Activity,
Zap,
BarChart3
} from "lucide-react";

import { motion } from "framer-motion";


const float1={
animate:{
y:[0,-18,0],
rotate:[12,18,12]
},
transition:{
duration:4,
repeat:Infinity,
ease:"easeInOut"
}
}

const float2={
animate:{
x:[0,16,0],
y:[0,-10,0]
},
transition:{
duration:4,
repeat:Infinity,
ease:"easeInOut"
}
}

const float3={
animate:{
y:[0,22,0],
rotate:[6,-4,6]
},
transition:{
duration:4,
repeat:Infinity,
ease:"easeInOut"
}
}

const float4={
animate:{
x:[0,-18,0],
y:[0,10,0]
},
transition:{
duration:4,
repeat:Infinity,
ease:"easeInOut"
}
}

const float5={
animate:{
y:[0,-12,0],
x:[0,8,0]
},
transition:{
duration:4,
repeat:Infinity,
ease:"easeInOut"
}
}

export default function KannadaHero(){

return(

<section className="
relative
min-h-screen
overflow-hidden
flex items-center
">


{/* 65 / 35 split */}
<div className="absolute inset-0 flex">
<div className="w-[65%] bg-emerald-600"></div>
<div className="w-[35%] bg-white"></div>
</div>



{/* glow */}
<div className="
absolute top-12 left-16
w-72 h-72
bg-white/10
rounded-full blur-3xl
"/>

<div className="
absolute bottom-8 left-1/3
w-96 h-96
bg-white/10
rounded-full blur-3xl
"/>




{/* Animated Cubes */}

<motion.div
{...float1}
className="
absolute
right-[12%]
top-24
w-24 h-24
bg-emerald-600
rounded-2xl
shadow-2xl
"
/>



<motion.div
{...float2}
className="
absolute
right-[28%]
top-44
w-14 h-14
bg-emerald-500
rounded-xl
shadow-xl
"
/>



<motion.div
{...float3}
className="
absolute
right-[10%]
top-[48%]
w-32 h-32
bg-emerald-700
rounded-3xl
shadow-2xl
"
/>



<motion.div
{...float4}
className="
absolute
right-[26%]
bottom-28
w-20 h-20
bg-emerald-500
rotate-45
rounded-2xl
shadow-xl
"
/>



<motion.div
{...float5}
className="
absolute
right-[8%]
bottom-16
w-10 h-10
bg-emerald-700
rounded-lg
"
/>




{/* animated connector lines */}
<motion.div
animate={{
opacity:[0.3,1,0.3]
}}
transition={{
duration:4,
repeat:Infinity
}}
className="
absolute right-[18%]
top-56 h-40
border-l
border-emerald-200/60
"
/>


<motion.div
animate={{
opacity:[0.2,.8,0.2]
}}
transition={{
duration:5,
repeat:Infinity
}}
className="
absolute right-[22%]
bottom-36
w-28
border-t
border-emerald-200/60
"
/>



<div className="
relative z-10
max-w-7xl mx-auto
px-6 w-full
">

<div className="max-w-3xl">


<p className="
uppercase
tracking-[4px]
text-green-100
font-semibold
mb-5
">
AI ಆಧಾರಿತ ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಬುದ್ಧಿಮತ್ತೆ
</p>



<h1 className="
text-5xl md:text-7xl
font-bold
mb-8
leading-tight
text-white
">

AI ಆಧಾರಿತ
ರೋಗಿ ತ್ರೈಯಾಜ್

<br/>

ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯಕ್ಕಾಗಿ

</h1>




<p className="
text-xl
text-green-100
mb-10
leading-relaxed
max-w-2xl
">
ಬುದ್ಧಿವಂತ ರೋಗಿ ನೋಂದಣಿ,
ರಿಯಲ್ ಟೈಮ್ ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ,
ವೈದ್ಯರ ಮಾರ್ಗೀಕರಣ
ಮತ್ತು ರೋಗ ಸ್ಫೋಟ ಮೇಲ್ವಿಚಾರಣೆ.
</p>





<div className="
flex flex-col
sm:flex-row
gap-5 mb-16
">


<a
href="/kn/intake"
className="
inline-flex
items-center justify-center
px-8 py-4
bg-white
text-emerald-700
font-bold
rounded-2xl
shadow-xl
hover:scale-105
transition
"
>

ರೋಗಿ ನೋಂದಣಿ ಆರಂಭಿಸಿ

<ArrowRight className="
ml-2 w-5 h-5
"/>

</a>




<a
href="#"
className="
inline-flex
items-center justify-center
px-8 py-4
bg-emerald-800/80
text-white
font-bold
rounded-2xl
border border-emerald-500
hover:bg-emerald-700
transition
"
>
ಡೆಮೋ ನೋಡಿ
</a>

</div>





{/* feature cards */}
<div className="
grid sm:grid-cols-3
gap-6
">


<div className="
bg-white/10
backdrop-blur-xl
rounded-3xl
p-6
border border-white/20
shadow-xl
">

<Activity className="
w-8 h-8 mb-4
"/>

<h3 className="
font-bold text-xl mb-2
">
ಸ್ಮಾರ್ಟ್ ನೋಂದಣಿ
</h3>

<p className="
text-green-100 text-sm
">
ವೇಗವಾದ ಲಕ್ಷಣ ಮತ್ತು ಜೀವಚಿಹ್ನೆ ಸಂಗ್ರಹ
</p>

</div>





<div className="
bg-white/10
backdrop-blur-xl
rounded-3xl
p-6
border border-white/20
shadow-xl
">

<Zap className="
w-8 h-8 mb-4
"/>

<h3 className="
font-bold text-xl mb-2
">
ತಕ್ಷಣ ತ್ರೈಯಾಜ್
</h3>

<p className="
text-green-100 text-sm
">
ರಿಯಲ್ ಟೈಮ್ ಅಪಾಯ ಸ್ಕೋರಿಂಗ್
</p>

</div>






<div className="
bg-white/10
backdrop-blur-xl
rounded-3xl
p-6
border border-white/20
shadow-xl
">

<BarChart3 className="
w-8 h-8 mb-4
"/>

<h3 className="
font-bold text-xl mb-2
">
ಮೇಲ್ವಿಚಾರಣೆ
</h3>

<p className="
text-green-100 text-sm
">
ರೋಗ ಸ್ಫೋಟ ಪತ್ತೆ
</p>

</div>




</div>

</div>
</div>

</section>

)

}