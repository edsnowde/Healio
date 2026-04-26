import {
AlertCircle,
CheckCircle,
AlertTriangle,
Clock
} from 'lucide-react'


interface Patient{
id:string
name:string
age:number
priority:'red'|'yellow'|'green'
riskScore:number
symptoms:string
assignedDoctor:string
intakeTime:string
estimatedWait:number
}

interface QueueBoardProps{
patients:Patient[]
}


export default function KannadaQueueBoard({
patients
}:QueueBoardProps){

const getPriorityIcon = (
priority:'red'|'yellow'|'green'
) => {

const icons = {
red: (
<AlertCircle className="w-5 h-5 text-priority-red"/>
),

yellow: (
<AlertTriangle className="w-5 h-5 text-priority-yellow"/>
),

green: (
<CheckCircle className="w-5 h-5 text-priority-green"/>
)
}

return icons[priority]

}



const getPriorityBg = (
priority:'red'|'yellow'|'green'
) => {

const colors = {
red:
'bg-priority-red/10 border-l-4 border-priority-red',

yellow:
'bg-priority-yellow/10 border-l-4 border-priority-yellow',

green:
'bg-priority-green/10 border-l-4 border-priority-green'
}

return colors[priority]

}



return(

<div className="
bg-white
rounded-xl
shadow-elevated
p-8
">

<h2 className="
text-2xl font-bold
text-gray-900 mb-6
">
ರೋಗಿ ಆದ್ಯತೆ ಸರದಿ
</h2>



<div className="space-y-3">

{
patients.map(
(patient,idx)=>(

<div
key={patient.id}
className={`
${getPriorityBg(patient.priority)}
rounded-lg p-4
transition-all hover:shadow-md
`}
>

<div className="
flex items-start
justify-between gap-4
">

<div className="
flex gap-4
items-start flex-1
">


<div className="
flex items-center justify-center
w-10 h-10
bg-gray-200
rounded-full
font-bold
">
{idx+1}
</div>



<div className="flex-1">

<div className="
flex items-center gap-2 mb-1
">

{
getPriorityIcon(
patient.priority
)
}

<h3 className="
font-bold text-gray-900
">
{patient.name}
</h3>

<span className="
text-xs bg-gray-200
px-2 py-1 rounded
">
{patient.age}ವ
</span>

</div>


<p className="
text-sm text-gray-600 mb-2
">
{patient.symptoms}
</p>


<div className="
flex gap-4
text-xs text-gray-600
">

<span>
ಅಪಾಯ:
<strong className="
text-gray-900
">
{" "}
{patient.riskScore}%
</strong>
</span>


<span>
ನೋಂದಣಿ:
<strong className="
text-gray-900
">
{" "}
{patient.intakeTime}
</strong>
</span>

</div>


</div>




<div className="text-right">

<p className="
text-xs text-gray-600 mb-1
">
ನಿಯೋಜಿತ ವೈದ್ಯರು
</p>

<p className="
font-bold text-sm
">
{patient.assignedDoctor}
</p>

</div>




<div className="
flex items-center gap-2
bg-white
px-3 py-2
rounded-lg
">

<Clock className="
w-4 h-4 text-gray-500
"/>

<span className="
font-bold
">
{patient.estimatedWait}
{" "}ನಿಮಿಷ
</span>

</div>


</div>



<button className="
px-3 py-2
bg-primary text-white
text-sm
font-medium
rounded
">
ವೀಕ್ಷಿಸಿ
</button>


</div>

</div>

))
}

</div>



{
patients.length===0 &&(

<div className="
text-center py-12
">
<p className="
text-gray-600
">
ಸರದಿಯಲ್ಲಿ ರೋಗಿಗಳಿಲ್ಲ
</p>
</div>

)
}

</div>

)

}