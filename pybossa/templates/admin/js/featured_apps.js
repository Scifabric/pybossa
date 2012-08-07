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
          if ($("#app" + app_id).hasClass("icon-star-empty")) {
              $("#app" + app_id).removeClass("icon-star-empty");
              $("#app" + app_id).addClass("icon-star");
          }
          if (!$("#appBtn" + app_id).hasClass('active')){
                $("#appBtn" + app_id).addClass('active');
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
          if ($("#app" + app_id).hasClass("icon-star")) {
              $("#app" + app_id).removeClass("icon-star");
              $("#app" + app_id).addClass("icon-star-empty");
          }
          if ($("#appBtn" + app_id).hasClass('active')){
                $("#appBtn" + app_id).removeClass('active');
          }
      });
  }

  function toggle(app_id) {
      if ($("#app" + app_id).hasClass("icon-star")) {
          del(app_id);
      }
      else {
          add(app_id);
      }
   }
</script>

