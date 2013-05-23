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
          $("#appBtnDel" + app_id).show();
          $("#appBtnAdd" + app_id).hide();
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
          $("#appBtnDel" + app_id).hide();
          $("#appBtnAdd" + app_id).show();

      });
  }
</script>

