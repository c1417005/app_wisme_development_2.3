const observer = document.getElementById('btn_research')

observer.addEventListener('click',() => {
    const word = document.getElementById('id_input_word').value;
    //再代入できないとダメでは
    if (word){
        console.log(word);
    }
    else{
        console.log("単語が入力されていません");
        return
    }


    fetch(`/wisme/search/mean/?word=${encodeURIComponent(word)}`)
    //バッククォートで囲む。URLにスペースは絶対に含めない。先頭にスラッシュ。
    //アプリは/wisme/の下にある。最初にそうやって設定したので、先頭に/wisme/
        .then(response => response.json())
        .then(data => {
            
            // const wordField = document.getElementById('id_searched_word');
            // const meaningField = document.getElementById('id_meaning');
            
            // if(meaningField){
            //     // wordField.value = word;
            //     meaningField.value = data.meaning;
            // }
            // //ここまでいらない

            const table = document.getElementById("words_table");
            const newRow = table.insertRow(-1);

            const cell1 = newRow.insertCell(0);
            const cell2 = newRow.insertCell(1);

            cell1.textContent = word;
            cell2.textContent = data.meaning;

            

        })
    });