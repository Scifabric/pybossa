<script type="text/javascript">
  var csrftoken = "{{ csrf_token() }}";

  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
  });

  $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
  function run(project_short_name, webhook_id) {
      $("#spin_" + webhook_id).addClass('fa-spin');
      $("#webhook_" + webhook_id).addClass('animated rotateIn');
      var url = $SCRIPT_ROOT + "/project/" + project_short_name + "/webhook/" + webhook_id;
      var xhr = $.ajax({
          type: 'POST',
          url: url,
          dataType: 'json',
      });
      xhr.done(function(data){
          console.log("Webhook ran!");
          $("#webhooks-refresh").show();
      });
  }

</script>
