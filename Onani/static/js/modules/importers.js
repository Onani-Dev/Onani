/**
 * @Author: kapsikkum
 * @Date:   2022-04-23 22:02:24
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2022-04-25 04:36:10
 */
class Importer {
  constructor() {
    this.importerInput = document.getElementById("post-importer-input");
    this.importerButton = document.getElementById("import-post-button");

    this.importerButton.onclick = () => {
      this.importPost(this.importerInput.value);
    };
  }

  get danbooruRegex() {
    return /https:\/\/danbooru\.donmai\.us\/posts\/(?<danbooruId>[\d]+)/;
  }

  addTags(data) {
    let tagInput = document.getElementById("file-tags");
    tagInput.value = "";
    // General tags
    for (let tag of data.tag_string_general.split(" ")) {
      tagInput.value += `${tag} `;
    }
    // Character tags
    for (let tag of data.tag_string_character.split(" ")) {
      tagInput.value += `char:${tag} `;
    }
    // Copyright tags
    for (let tag of data.tag_string_copyright.split(" ")) {
      tagInput.value += `cop:${tag} `;
    }
    //  Artist tags
    for (let tag of data.tag_string_artist.split(" ")) {
      tagInput.value += `art:${tag} `;
    }
  }

  addFile(data) {
    let filesInput = document.getElementById("file-upload");
    fetch(data.file_url, { method: "GET" })
      .then((response) => response.blob())
      .then((blob) => {
        let file = new File([blob], data.file_url.split("/")[-1], {
          type: blob.type,
          lastModified: new Date().getTime(),
        });
        let container = new DataTransfer();
        container.items.add(file);
        filesInput.files = container.files;
        let event = new Event("change");
        filesInput.dispatchEvent(event);
      })
      .catch((error) => console.error(error));
  }

  addSource(data) {
    let fileSource = document.getElementById("file-source");
    fileSource.value = data.source;
  }

  importPost(string) {
    if (!this.danbooruRegex.test(string)) {
      alert("Invalid.");
      this.importerInput.value = "";
    }
    let match = this.danbooruRegex.exec(string)[1];

    fetch(`https://danbooru.donmai.us/posts/${match}.json`, { method: "GET" })
      .then((response) => response.json())
      .then((json) => {
        this.addTags(json);
        this.addFile(json);
        this.addSource(json);
      })
      .catch((error) => console.error(error));
  }
}

export { Importer };
