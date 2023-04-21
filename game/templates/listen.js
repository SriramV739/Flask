socket.on('gotofollowup', function(data){
        if (gid==data.gid){
            var qn=data.q
            var locto="/playerfollowup/{{playerid}}/"+gid+"/"+qn;
            window.location.href=locto;
        }
    });

socket.on('timeup',function(data){
    if(gid==data.gid){
        var qn=data.q
        var locto="/resultplayer/{{playerid}}/"+gid+"/"+qn;
        window.location.href=locto;
    }
});

socket.on('gotolb',function(data){
    if(gid==data.gid){
        var qn=data.q
        var locto="/leaderboardp/{{playerid}}/"+gid+"/"+qn;
        window.location.href=locto;
    }
});

socket.on('gotonextq',function(data){
    if(gid==data.gid){
        var qn=Number(data.q)+1
        var locto="/question/{{playerid}}/"+gid+"/"+qn;
        window.location.href=locto;
    }
});
