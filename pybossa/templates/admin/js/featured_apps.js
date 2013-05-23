<script type=text/javascript>
  $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
  function add(app_id) {
      var url = $SCRIPT_ROOT + "/admin/featured/" + app_id;
      var xhr = $.ajax({
          type: 'POST',
          url: url,
          dataType: 'json',
      });
      xhr.done(function(){
          if ($("#app" + app_id).hasClass("icon-plus")) {
              $("#app" + app_id).removeClass("icon-plus");
              $("#app" + app_id).addClass("icon-remove");
          }
          if ($("#appBtn" + app_id).hasClass('btn btn-primary')){
                $("#appBtn" + app_id).removeClass('btn btn-primary');
                $("#appBtn" + app_id).addClass('btn btn-danger');
          }
      });
  }
  function del(app_id) {
      var url = $SCRIPT_ROOT + "/admin/featured/" + app_id;
      var xhr = $.ajax({
          type: 'DELETE',
          url: url,
          dataType: 'json',
      });
      xhr.done(function(){
          if ($("#app" + app_id).hasClass("icon-remove")) {
              $("#app" + app_id).removeClass("icon-remove");
              $("#app" + app_id).addClass("icon-plus");
          }
          if ($("#appBtn" + app_id).hasClass('btn btn-danger')){
                $("#appBtn" + app_id).removeClass('btn btn-danger');
                $("#appBtn" + app_id).addClass('btn btn-primary');
          }
      });
  }

  function toggle(app_id) {
      if ($("#app" + app_id).hasClass("icon-remove")) {
          del(app_id);
      }
      else {
          add(app_id);
      }
   }
</script>

