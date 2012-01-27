// Copyright (C) Daniel Lombraña González 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//

// Gets the application name and gets all its tasks 
function getApp(name) {
    app_id = null;
    $.getJSON('/api/app', function(apps) {
            $.each(apps, function(){
                if (this.short_name == name) {
                    app_id = this.id;
                    $("#question h1").text(this.description);
                }
            });
            getTask(app_id);
    });
}

// Get all the tasks for a given application. Selects one task randomly
function getTask(app_id) {
    previous_task_id = $("#task-id").text();
    app_id_tasks = [];
    $.getJSON('/api/task', function(all_tasks){
        $.each(all_tasks, function(){
            if ((this.app_id == app_id) & (this.state != "1")) {
                app_id_tasks.push(this);    
            }
            });
        if (app_id_tasks.length >= 1) {
                $.each(app_id_tasks, function(){
                    if (previous_task_id != "#"){
                    app_id_tasks = jQuery.grep(app_id_tasks, function(value) {
                            return value != previous_task_id;
                            });
                    }

                    task = app_id_tasks[Math.floor(Math.random()*app_id_tasks.length)];

                    if ((task.app_id == app_id) & (task.state == "0")) {
                    $("#photo-link").attr("href", task.info.link);
                    $("#photo").attr("src",task.info.url);
                    $("#task-id").text(task.id);
                    return false;
                    }
                    });
        }
        else {

                $("#question").hide();
                $("#answer").hide();
                $("#finish").fadeIn();
        }
    });
}

// Saves the answer for the given task
function submitTask(answer) {
    task_id = $("#task-id").text();
    url = '/api/task/' + task_id;
    $.getJSON(url, function(task){
            // Task completed
            task.state = "1"
            // Update the state of the task in the DB
            $.ajax({
                type: 'PUT',
                dataType: 'json',
                url: url, 
                data: JSON.stringify(task),
                contentType: 'application/json',
                success: function() { 
                        taskrun = {
                        'created': task.create_time,
                        'app_id': task.app_id,
                        'task_id': task.id,
                        'info': {'answer': answer }
                        };

                        // Convert it to a string
                        taskrun = JSON.stringify(taskrun);

                        $.ajax({
                            type: 'POST',
                            dataType: 'json',
                            url: '/api/taskrun', 
                            data: taskrun,
                            contentType: 'application/json',
                            success: function() { 
                                        $("#success").fadeIn();
                                        setTimeout(function() {
                                            $("#success").fadeOut();
                                            }, 1000);
                                        getApp("flickrperson");
                                     }
                        });

                         }
            });


    });
}

getApp("flickrperson");
