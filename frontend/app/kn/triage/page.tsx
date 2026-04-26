'use client'

import { useState,useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface AnalysisStep{
agent:string
status:'pending'|'running'|'complete'
}

export default function KannadaTriagePage(){

const router=useRouter()

const [steps,setSteps]=useState<AnalysisStep[]>([
{
agent:'ಏಜೆಂಟ್ 1: ನೋಂದಣಿ ಪರಿಶೀಲನೆ',
status:'running'
},
{
agent:'ಏಜೆಂಟ್ 2: ಅಪಾಯ ಮೌಲ್ಯಮಾಪನ',
status:'pending'
},
{
agent:'ಏಜೆಂಟ್ 3: ವೈದ್ಯರಿಗೆ ಮಾರ್ಗೀಕರಣ',
status:'pending'
}
])

const [complete,setComplete]=useState(false)
const [isLoading,setIsLoading]=useState(true)
const [error,setError]=useState('')

const [triageResult,setTriageResult]=useState<any>(null)



useEffect(()=>{

const formDataStr=
sessionStorage.getItem(
'patientFormData'
)

if(!formDataStr){

setError(
'ರೋಗಿಯ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ'
)

setTimeout(
()=>router.push('/kn/intake'),
2000
)

setIsLoading(false)
return
}

const formData=
JSON.parse(formDataStr)



const timeline=[
{index:0,delay:800},
{index:1,delay:2200},
{index:2,delay:3600}
]

timeline.forEach(
({index,delay})=>{

setTimeout(()=>{

setSteps(prev=>{

const updated=[...prev]

if(index>0){
updated[index-1]={
...updated[index-1],
status:'complete'
}
}

updated[index]={
...updated[index],
status:'running'
}

return updated

})

},delay)

})



setTimeout(()=>{

setSteps(
prev=>prev.map(
step=>({
...step,
status:'complete'
})
)
)


setTriageResult({

patientId:
`PAT-2626-${Math.random()
.toString()
.slice(2,6)}`,

riskScore:89,

priority:'Red',

doctor:'Dr. Rahul Verma',

summary:
`${formData.symptoms}
ಆಧರಿಸಿ ತುರ್ತು ಪರಿಶೀಲನೆ ಅಗತ್ಯ.`,

recommendations:[
'ತಕ್ಷಣ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ',
'24 ಗಂಟೆಗಳೊಳಗೆ ಫಾಲೋಅಪ್'
],

outbreak:true,

clusterAlert:
'ಸಮಾನ ಲಕ್ಷಣ ಗುಂಪು ಪತ್ತೆ'
})

setComplete(true)
setIsLoading(false)

},4200)

}

,[])



const priorityColor=
triageResult?.priority==="Red"
? "border-red-500 bg-red-50"
: triageResult?.priority==="Yellow"
? "border-yellow-500 bg-yellow-50"
: "border-green-500 bg-green-50"



return(

<main className="
min-h-screen
py-12
px-6
bg-gradient-to-br
from-slate-50
to-slate-100
">

<div className="
max-w-4xl
mx-auto
">


{/* Agent Progress */}
<div className="
bg-white
rounded-xl
shadow-elevated
p-8
mb-8
">

<h2 className="
text-2xl
font-bold
mb-6
">
AI ತ್ರೈಯಾಜ್ ವಿಶ್ಲೇಷಣೆ
</h2>


<div className="space-y-4">

{steps.map(
(step,idx)=>(

<div
key={idx}
className="
flex items-center gap-4
"
>

<div className={`
w-8 h-8 rounded-full
flex items-center justify-center
font-bold text-sm

${
step.status==="complete"
? 'bg-green-600 text-white'
:step.status==="running"
? 'bg-emerald-600 text-white animate-pulse'
:'bg-gray-200'
}
`}>

{
step.status==="running"
&&
<Loader2 className="
w-5 h-5 animate-spin
"/>
}

{
step.status==="complete"
&& "✓"
}

{
step.status==="pending"
&& idx+1
}

</div>


<div className="flex-1">

<p className="
font-semibold
">
{step.agent}
</p>

{
step.status==="running"
&&(
<p className="
text-sm text-gray-500
">
ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ...
</p>
)
}

</div>


<span className="
text-xs
px-3 py-1
rounded-full
bg-gray-100
">
{
step.status==="running"
? "ಚಾಲನೆಯಲ್ಲಿದೆ"
:step.status==="complete"
? "ಪೂರ್ಣ"
:"ಬಾಕಿ"
}
</span>

</div>

))
}

</div>



{
complete && (

<div className="
mt-6 p-4
bg-green-50
border border-green-500
rounded-lg
">
<p className="
text-green-700 font-semibold
">
✓ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣ
</p>
</div>

)
}

</div>



{error && (
<div className="
bg-red-50
border border-red-500
rounded-lg
p-4 mb-8
">
{error}
</div>
)}




{/* Result */}
{
triageResult && (

<div className="space-y-6">


<div className={`
border-l-4
rounded-2xl
p-8
shadow-lg
${priorityColor}
`}>

<h2 className="
text-2xl font-bold mb-4
">
ತ್ರೈಯಾಜ್ ಫಲಿತಾಂಶ
</h2>


<div className="
grid md:grid-cols-2 gap-6
">

<div>
<p className="mb-2">
<strong>ರೋಗಿ ID:</strong>
{" "}
{triageResult.patientId}
</p>

<p className="mb-2">
<strong>ಅಪಾಯ ಸ್ಕೋರ್:</strong>
{" "}
{triageResult.riskScore}%
</p>

<p className="mb-2">
<strong>ಆದ್ಯತೆ:</strong>
{" "}
{triageResult.priority}
</p>

</div>


<div>
<p className="mb-2">
<strong>ನಿಯೋಜಿತ ವೈದ್ಯರು:</strong>
{" "}
{triageResult.doctor}
</p>

<p>
<strong>ಸಾರಾಂಶ:</strong>
<br/>
{triageResult.summary}
</p>

</div>


</div>


<div className="mt-6">
<h3 className="
font-bold mb-3
">
ಶಿಫಾರಸುಗಳು
</h3>

<ul className="
list-disc pl-6
space-y-2
">

{
triageResult.recommendations.map(
(rec:any,i:number)=>(
<li key={i}>
{rec}
</li>
))
}

</ul>
</div>


</div>




{
triageResult.outbreak && (

<div className="
bg-red-50
border-l-4 border-red-500
rounded-xl
p-6
">

<h3 className="
font-bold text-red-700 mb-3
">
⚠ ರೋಗ ಸ್ಫೋಟ ಎಚ್ಚರಿಕೆ
</h3>

<p>
{triageResult.clusterAlert}
</p>

</div>

)
}




<div className="flex gap-4">

<Link
href="/kn/dashboard"
className="
flex-1
px-6 py-3
bg-emerald-600
text-white
font-bold
rounded-lg
text-center
"
>
ವೈದ್ಯರ ಸರದಿ ನೋಡಿ
</Link>


<Link
href="/kn/intake"
className="
flex-1
px-6 py-3
bg-gray-200
font-bold
rounded-lg
text-center
"
>
ಹೊಸ ರೋಗಿ
</Link>


</div>

</div>

)
}



{
isLoading && !triageResult && (

<div className="
text-center py-12
">

<Loader2 className="
w-8 h-8
animate-spin
mx-auto mb-4
text-emerald-600
"/>

<p className="text-gray-600">
ರೋಗಿಯ ಮಾಹಿತಿ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...
</p>

</div>

)
}


</div>

</main>

)

}