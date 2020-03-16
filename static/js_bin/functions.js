function change_select() {
                            $.getJSON("http://suffolkbriefbank.pythonanywhere.com/getjson/", { venues: $("select[name='body']").val()},
                                function(data){
                                    $("select[name='venue']").empty();
                                    if(data.length > 0){
                                        $("select[name='venue']").append("<option value='none' selected disabled hidden> Select an Option </option>");
                                        var i;
                                        for(i = 0; i < data.length; i++){
                                            $("select[name='venue']").append("<option value ='"+ data[i][1] + "'>" + data[i][0] + "</option>");
                                        }
                                        $("label[name='venue']").show()
                                    }else{
                                        $("label[name='venue']").hide()
                                    }
                                });
                        };
$(document).ready(function(){
  $("input[class='main']").click(function(){
    $("div[class='"+ $(this).attr('name') +"']").slideToggle(200);
    $("div[class='"+ $(this).attr('name') +"']").childern().prop("checked", false);
  });
});