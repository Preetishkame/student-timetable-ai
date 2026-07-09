// =========================================
// Smart Timetable AI
// dashboard.js
// Part 1
// =========================================

const API = "/api";


// -----------------------------------------
// API REQUEST
// -----------------------------------------

async function apiRequest(endpoint, method = "GET", data = null) {

    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(API + endpoint, options);

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.message || "Request Failed");
    }

    return result;

}



// -----------------------------------------
// PAGE LOAD
// -----------------------------------------





// -----------------------------------------
// INITIALIZE
// -----------------------------------------

async function initializeDashboard() {

    try {

        showLoading();

        await loadUser();

        await loadDashboard();

        await loadTodayTimetable();

        await loadUpcomingExams();

        await loadPendingAssignments();

        hideLoading();

    }

    catch (err) {

        console.error(err);

        hideLoading();

        showToast("Unable to load dashboard", "error");

    }

}



// -----------------------------------------
// LOAD USER
// -----------------------------------------

async function loadUser() {

    const user = await apiRequest("/user");

    document.getElementById("welcome-user").textContent =
        user.name;

    document.getElementById("studentName").textContent =
        user.name;

    const profileName = document.getElementById("profileName");

    if (profileName)
        profileName.textContent = user.name;

    const profileEmail = document.getElementById("profileEmail");

    if (profileEmail)
        profileEmail.textContent = user.email;

}



// -----------------------------------------
// DASHBOARD SUMMARY
// -----------------------------------------

async function loadDashboard() {

    const data =
        await apiRequest("/dashboard/summary");

    document.getElementById("subjectCount").textContent =
        data.subjects;

    document.getElementById("assignmentCount").textContent =
        data.assignments;

    document.getElementById("homeworkCount").textContent =
        data.homework;

    document.getElementById("examCount").textContent =
        data.exams;

    document.getElementById("attendancePercent").textContent =
        data.attendance;

    document.getElementById("attendanceBar").style.width =
        data.attendance + "%";

}



// -----------------------------------------
// TODAY TIMETABLE
// -----------------------------------------

async function loadTodayTimetable() {

    const table =
        document.getElementById("todayTimetable");

    if (!table) return;

    const timetable =
        await apiRequest("/timetable/today");

    if (timetable.length === 0) {

        table.innerHTML = `
        <tr>
            <td colspan="2">
                No timetable today.
            </td>
        </tr>`;

        return;

    }

    table.innerHTML = "";

    timetable.forEach(item => {

        table.innerHTML += `

        <tr>

            <td>

                ${item.start_time}
                -
                ${item.end_time}

            </td>

            <td>

                ${item.subject}

            </td>

        </tr>

        `;

    });

}
// =========================================
// PART 2
// SUBJECT MANAGEMENT
// =========================================


// -----------------------------------------
// LOAD SUBJECTS
// -----------------------------------------

async function loadSubjects() {

    const table =
    document.getElementById("subjectTable");

    if(!table) return;

    const subjects =
    await apiRequest("/subjects");

    if(subjects.length===0){

        table.innerHTML=`

        <tr>

            <td colspan="4">

                No subjects added.

            </td>

        </tr>

        `;

        return;

    }

    table.innerHTML="";

    subjects.forEach(subject=>{

        table.innerHTML+=`

        <tr>

            <td>

                ${subject.subject_name}

            </td>

            <td>

                ${subject.difficulty}

            </td>

            <td>

                ${subject.study_hours} hrs

            </td>

            <td>

                <button
                class="btn-danger"
                onclick="deleteSubject(${subject.id})">

                Delete

                </button>

            </td>

        </tr>

        `;

    });

}



// -----------------------------------------
// ADD SUBJECT
// -----------------------------------------

const subjectForm =
document.getElementById("subjectForm");

if(subjectForm){

subjectForm.addEventListener("submit",

async function(e){

    e.preventDefault();

    try{

        showLoading();

        await apiRequest(

            "/subjects",

            "POST",

            {

                subject:
                document.getElementById("subjectName").value,

                difficulty:
                document.getElementById("difficulty").value,

                hours:
                document.getElementById("studyHours").value

            }

        );

        subjectForm.reset();

        await loadSubjects();

        hideLoading();

        showToast(
            "Subject Added"
        );

    }

    catch(err){

        hideLoading();

        showToast(
            err.message,
            "error"
        );

    }

});

}



// -----------------------------------------
// DELETE SUBJECT
// -----------------------------------------

async function deleteSubject(id){

    if(!confirmDelete()) return;

    try{

        await apiRequest(

            "/subjects/"+id,

            "DELETE"

        );

        loadSubjects();

        showToast(
            "Subject Deleted"
        );

    }

    catch(err){

        showToast(
            err.message,
            "error"
        );

    }

}



// =========================================
// AI TIMETABLE
// =========================================


// -----------------------------------------
// GENERATE
// -----------------------------------------

const generateBtn =
document.getElementById("generateBtn");

if(generateBtn){

generateBtn.addEventListener("click",

async ()=>{

    try{

        showLoading();

        await apiRequest(

            "/timetable/generate",

            "POST"

        );

        await loadGeneratedTimetable();

        await loadTodayTimetable();

        hideLoading();

        showToast(
            "AI Timetable Generated"
        );

    }

    catch(err){

        hideLoading();

        showToast(
            err.message,
            "error"
        );

    }

});

}



// -----------------------------------------
// LOAD TIMETABLE
// -----------------------------------------

async function loadGeneratedTimetable(){

    const table=
    document.getElementById("generatedTable");

    if(!table) return;

    const timetable=
    await apiRequest("/timetable");

    if(timetable.length===0){

        table.innerHTML=`

        <tr>

            <td colspan="4">

                No timetable generated.

            </td>

        </tr>

        `;

        return;

    }

    table.innerHTML="";

    timetable.forEach(item=>{

        table.innerHTML+=`

        <tr>

            <td>

                ${item.day}

            </td>

            <td>

                ${item.subject}

            </td>

            <td>

                ${item.start_time}

            </td>

            <td>

                ${item.end_time}

            </td>

        </tr>

        `;

    });

}



// -----------------------------------------
// INITIAL LOAD (subjects & timetable run when AI tab is first visited)
// -----------------------------------------
// =========================================
// PART 3
// HOMEWORK & ASSIGNMENTS
// =========================================



// =========================================
// HOMEWORK
// =========================================


// ------------------------------
// LOAD HOMEWORK
// ------------------------------

async function loadHomework(){

    const table =
    document.getElementById("homeworkTable");

    if(!table) return;

    const homework =
    await apiRequest("/homework");

    if(homework.length===0){

        table.innerHTML=`
        <tr>
            <td colspan="5">
                No homework found.
            </td>
        </tr>
        `;

        return;

    }

    table.innerHTML="";

    homework.forEach(hw=>{

        table.innerHTML+=`

        <tr>

            <td>${hw.title}</td>

            <td>${hw.subject}</td>

            <td>${hw.due_date}</td>

            <td>${hw.status}</td>

            <td>

                <button
                class="btn-danger"
                onclick="deleteHomework(${hw.id})">

                Delete

                </button>

            </td>

        </tr>

        `;

    });

}



// ------------------------------
// ADD HOMEWORK
// ------------------------------

const homeworkForm =
document.getElementById("addHomeworkForm");

if(homeworkForm){

homeworkForm.addEventListener("submit",

async function(e){

    e.preventDefault();

    try{

        await apiRequest(

            "/homework",

            "POST",

            {

                title:
                document.getElementById("hwTitle").value,

                subject:
                document.getElementById("hwSubject").value,

                due_date:
                document.getElementById("hwDue").value

            }

        );

        homeworkForm.reset();

        loadHomework();

        showToast("Homework Added");

    }

    catch(err){

        showToast(err.message,"error");

    }

});

}



// ------------------------------
// DELETE HOMEWORK
// ------------------------------

async function deleteHomework(id){

    if(!confirmDelete()) return;

    await apiRequest(

        "/homework/"+id,

        "DELETE"

    );

    loadHomework();

    showToast("Homework Deleted");

}



// =========================================
// ASSIGNMENTS
// =========================================


// ------------------------------
// LOAD ASSIGNMENTS
// ------------------------------

async function loadAssignments(){

    const table =
    document.getElementById("assignmentTable");

    if(!table) return;

    const assignments =
    await apiRequest("/assignments");

    if(assignments.length===0){

        table.innerHTML=`

        <tr>

            <td colspan="5">

                No assignments found.

            </td>

        </tr>

        `;

        return;

    }

    table.innerHTML="";

    assignments.forEach(item=>{

        table.innerHTML+=`

        <tr>

            <td>${item.title}</td>

            <td>${item.subject}</td>

            <td>${item.due_date}</td>

            <td>${item.status}</td>

            <td>

                <button
                class="btn-danger"
                onclick="deleteAssignment(${item.id})">

                Delete

                </button>

            </td>

        </tr>

        `;

    });

}



// ------------------------------
// ADD ASSIGNMENT
// ------------------------------

const assignmentForm =
document.getElementById("addAssignmentForm");

if(assignmentForm){

assignmentForm.addEventListener("submit",

async function(e){

    e.preventDefault();

    try{

        await apiRequest(

            "/assignments",

            "POST",

            {

                title:
                document.getElementById("assignmentTitle").value,

                subject:
                document.getElementById("assignmentSubject").value,

                due_date:
                document.getElementById("assignmentDue").value

            }

        );

        assignmentForm.reset();

        loadAssignments();

        showToast("Assignment Added");

    }

    catch(err){

        showToast(err.message,"error");

    }

});

}



// ------------------------------
// DELETE ASSIGNMENT
// ------------------------------

async function deleteAssignment(id){

    if(!confirmDelete()) return;

    await apiRequest(

        "/assignments/"+id,

        "DELETE"

    );

    loadAssignments();

    showToast("Assignment Deleted");

}



// =========================================
// PENDING ASSIGNMENTS (dashboard widget)
// =========================================

async function loadPendingAssignments() {

    const container =
    document.getElementById("pendingAssignments");

    if (!container) return;

    try {

        const assignments =
        await apiRequest("/assignments/pending");

        if (assignments.length === 0) {

            container.innerHTML = "No pending assignments.";
            return;

        }

        container.innerHTML = "";

        assignments.forEach(item => {

            container.innerHTML += `
            <div class="list-item">
                <strong>${item.title}</strong><br>
                ${item.subject} — Due: ${item.due_date}
            </div>`;

        });

    } catch (err) {

        console.error("loadPendingAssignments:", err);

    }

}
// =========================================
// PART 4
// EXAMS & ATTENDANCE
// =========================================



// =========================================
// EXAMS
// =========================================


// ------------------------------
// LOAD EXAMS
// ------------------------------

async function loadExams(){

    const table =
    document.getElementById("examTable");

    if(!table) return;

    const exams =
    await apiRequest("/exams");

    if(exams.length===0){

        table.innerHTML=`

        <tr>

            <td colspan="5">

                No exams added.

            </td>

        </tr>

        `;

        return;

    }

    table.innerHTML="";

    exams.forEach(exam=>{

        table.innerHTML+=`

        <tr>

            <td>${exam.subject}</td>

            <td>${exam.exam_date}</td>

            <td>${exam.days_left}</td>

            <td>${exam.status}</td>

            <td>

                <button
                class="btn-danger"
                onclick="deleteExam(${exam.id})">

                Delete

                </button>

            </td>

        </tr>

        `;

    });

}



// ------------------------------
// ADD EXAM
// ------------------------------

const examForm =
document.getElementById("addExamForm");

if(examForm){

examForm.addEventListener("submit",

async function(e){

    e.preventDefault();

    try{

        await apiRequest(

            "/exams",

            "POST",

            {

                subject:
                document.getElementById("examSubject").value,

                exam_date:
                document.getElementById("examDate").value

            }

        );

        examForm.reset();

        loadExams();

        loadUpcomingExams();

        loadDashboard();

        showToast("Exam Added");

    }

    catch(err){

        showToast(err.message,"error");

    }

});

}



// ------------------------------
// DELETE EXAM
// ------------------------------

async function deleteExam(id){

    if(!confirmDelete()) return;

    await apiRequest(

        "/exams/"+id,

        "DELETE"

    );

    loadExams();

    loadUpcomingExams();

    loadDashboard();

    showToast("Exam Deleted");

}



// ------------------------------
// UPCOMING EXAMS
// ------------------------------

async function loadUpcomingExams(){

    const container =
    document.getElementById("upcomingExams");

    if(!container) return;

    const exams =
    await apiRequest("/exams/upcoming");

    if(exams.length===0){

        container.innerHTML=

        "No upcoming exams.";

        return;

    }

    container.innerHTML="";

    exams.forEach(exam=>{

        container.innerHTML+=`

        <div class="list-item">

            <strong>

                ${exam.subject}

            </strong>

            <br>

            ${exam.exam_date}

        </div>

        `;

    });

}



// =========================================
// ATTENDANCE
// =========================================


// ------------------------------
// LOAD ATTENDANCE
// ------------------------------

async function loadAttendance(){

    const data =
    await apiRequest("/attendance");

    document.getElementById(
        "attendancePercentage"
    ).textContent =
    data.percentage;

    document.getElementById(
        "attendanceProgress"
    ).style.width =
    data.percentage+"%";

    document.getElementById(
        "attendanceStatus"
    ).textContent =
    data.status;

    document.getElementById(
        "classesNeeded"
    ).textContent =
    data.need;

    const history =
    document.getElementById(
        "attendanceHistory"
    );

    if(history){

        history.innerHTML=`

        <tr>

            <td>

                ${data.attended}

            </td>

            <td>

                ${data.total}

            </td>

            <td>

                ${data.percentage}%

            </td>

            <td>

                ${data.status}

            </td>

        </tr>

        `;

    }

}



// ------------------------------
// SAVE ATTENDANCE
// ------------------------------

const attendanceForm =
document.getElementById(
"attendanceForm"
);

if(attendanceForm){

attendanceForm.addEventListener(

"submit",

async function(e){

    e.preventDefault();

    try{

        await apiRequest(

            "/attendance",

            "POST",

            {

                attended:
                document.getElementById("attended").value,

                total:
                document.getElementById("totalClasses").value

            }

        );

        loadAttendance();

        loadDashboard();

        showToast(
            "Attendance Updated"
        );

    }

    catch(err){

        showToast(
            err.message,
            "error"
        );

    }

});

}



// =========================================
// SETTINGS PAGE BUTTONS
// =========================================

const settingsThemeToggle =
document.getElementById("settingsThemeToggle");

if (settingsThemeToggle) {

    settingsThemeToggle.addEventListener("click", () => {

        const dark =
        document.documentElement.getAttribute("data-theme");

        if (dark === "dark") {

            document.documentElement.removeAttribute("data-theme");
            localStorage.setItem("theme", "light");

        } else {

            document.documentElement.setAttribute("data-theme", "dark");
            localStorage.setItem("theme", "dark");

        }

    });

}

const settingsLogoutBtn =
document.getElementById("settingsLogoutBtn");

if (settingsLogoutBtn) {

    settingsLogoutBtn.addEventListener("click", async () => {

        await fetch("/logout");
        window.location = "/login";

    });

}
// =========================================
// PART 5
// FINAL
// =========================================



// =========================================
// LOGOUT
// =========================================

const logoutBtn =
document.getElementById("logoutBtn");

if(logoutBtn){

logoutBtn.addEventListener("click",

async ()=>{

    try{

        await fetch("/logout");

        window.location="/login";

    }

    catch(err){

        console.log(err);

    }

});

}



// =========================================
// SEARCH SUBJECT
// =========================================

const searchBox =
document.getElementById("searchBox");

if(searchBox){

searchBox.addEventListener(

"keyup",

async function(){

    const keyword=this.value;

    try{

        const subjects=
        await apiRequest(
            "/subjects/search?q="+keyword
        );

        const table=
        document.getElementById(
            "subjectTable"
        );

        if(subjects.length===0){

            table.innerHTML=`

            <tr>

            <td colspan="4">

            No Subject Found

            </td>

            </tr>

            `;

            return;

        }

        table.innerHTML="";

        subjects.forEach(subject=>{

            table.innerHTML+=`

            <tr>

                <td>

                ${subject.subject_name}

                </td>

                <td>

                ${subject.difficulty}

                </td>

                <td>

                ${subject.study_hours}

                </td>

                <td>

                <button
                class="btn-danger"
                onclick="deleteSubject(${subject.id})">

                Delete

                </button>

                </td>

            </tr>

            `;

        });

    }

    catch(err){

        console.log(err);

    }

});

}



// =========================================
// TAB NAVIGATION
// =========================================

const tabs=
document.querySelectorAll(".sidebar a");

tabs.forEach(tab=>{

tab.addEventListener("click",

function(e){

    e.preventDefault();

    const target=
    this.getAttribute("data-tab");

    document
    .querySelectorAll(".tab-content")

    .forEach(page=>{

        page.style.display="none";

    });

    const section=
    document.getElementById(

        target

    );

    if(section){

        section.style.display="block";

    }

    tabs.forEach(btn=>{

        btn.classList.remove("active");

    });

    this.classList.add("active");

});

});




// =========================================
// REFRESH BUTTON
// =========================================

const refreshBtn=
document.getElementById(

"refreshDashboard"

);

if(refreshBtn){

refreshBtn.addEventListener(

"click",

async ()=>{

    showLoading();

    await initializeDashboard();

    await loadSubjects();

    await loadHomework();

    await loadAssignments();

    await loadExams();

    await loadAttendance();

    await loadGeneratedTimetable();

    hideLoading();

    showToast(

        "Dashboard Updated"

    );

});

}



// =========================================
// AUTO REFRESH
// =========================================

setInterval(()=>{

    loadDashboard();

    loadAttendance();

    loadUpcomingExams();

    loadPendingAssignments();

},60000);




// =========================================
// GLOBAL ERROR
// =========================================

window.addEventListener(

"unhandledrejection",

function(event){

    console.error(

        event.reason

    );

});




// =========================================
// START — single authoritative boot sequence
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    initializeDashboard();

    loadSubjects();

    loadHomework();

    loadAssignments();

    loadExams();

    loadAttendance();

    loadGeneratedTimetable();

});
