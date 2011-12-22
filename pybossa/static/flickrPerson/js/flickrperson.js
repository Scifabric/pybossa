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

// Gets the application name and gets all its task batches
function getApp(name) {
    app_id = null;
    $.getJSON('/api/app', function(apps) {
            $.each(apps, function(){
                if (this.short_name == name) {
                    app_id = this.id;
                    $("#question h1").text(this.description);
                }
            });
            getBatches(app_id);
    });
}

// Gets all the batches for a given application, and selects one randomly to get all its tasks
function getBatches(app_id) {
    app_id_batches = [];
    $.getJSON('/api/batch', function(all_batches){
            $.each(all_batches, function(){
                if (this.app_id == app_id) {
                    app_id_batches.push(this);
                }
            });
            batch = app_id_batches[Math.floor(Math.random()*app_id_batches.length)];
            $("#batch-id").text(batch.id);
            getTask(app_id, batch.id);
    });
}

// Get all the tasks for a given application and its associated batch. Selects one task randomly
function getTask(app_id, batch_id) {
    previous_task_id = $("#task-id").text();
    app_id_tasks = [];
    $.getJSON('/api/task', function(all_tasks){
        $.each(all_tasks, function(){
            if ((this.app_id == app_id) & (this.batch_id == batch_id)) {
                app_id_tasks.push(this);    
            }
            });
        $.each(app_id_tasks, function(){
            if (previous_task_id != "#"){
            app_id_tasks = jQuery.grep(app_id_tasks, function(value) {
                    return value != previous_task_id;
                    });
            }

            task = app_id_tasks[Math.floor(Math.random()*app_id_tasks.length)];

            if ((task.app_id == app_id) & (task.batch_id == batch_id) & (task.state == 0)) {
            $("#photo-link").attr("href", task.info.link);
            $("#photo").attr("src",task.info.url);
            $("#task-id").text(task.id);
            return false;
            }

            });
    });
}

// Saves the answer for the given task
function submitTask(answer) {
    task_id = $("#task-id").text();
    url = '/api/task/' + task_id;
    $.getJSON(url, function(task){
            taskrun = {
            'create_time': task.create_time,
            'app_id': task.app_id,
            'job_id': task.id,
            'user_id': 0,
            'batch_id': task.batch_id,
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
                            getApp("FlickrPerson");
                         }
            });
    });
}

getApp("FlickrPerson");
