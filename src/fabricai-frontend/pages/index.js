import Dropdown from "react-dropdown";
import Image from "next/image";
import { useState } from "react";

const SideBar = ({ articles }) => {
  return (
    <div className="w-[20%] bg-[#088395] flex flex-col content-center text-center relative">
      <Dropdown
        options={articles}
        className="w-[80%] bg-[#D9D9D9] p-2 mt-16 text-[#0A4D68] mx-auto"
      />
      <h2 className="mt-32">Text Based Edit</h2>
      <input className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto" />
      <h2 className="mt-32">Image Based Edit</h2>
      <input
        type="file"
        className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto"
      />
      <button className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto">
        Submit
      </button>
      <Image
        src={"/fabric.ai.png"}
        width={120}
        height={200}
        className="absolute bottom-8 left-0 right-0 ml-auto mr-auto"
      />
    </div>
  );
};

export default function Home() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [image, setImage] = useState(null);
  const [articles, setArticles] = useState([]);

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        "https://c2ae-108-234-21-0.ngrok-free.app/upload_image",
        {
          method: "POST",
          body: formData,
        }
      )
        .then((res) => res.json())
        .then((data) => {
          console.log(data);
          setArticles(data["articles_detected"]);
          setImage(selectedFile);
        });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <>
      <div className="h-screen w-screen flex flex-row justify-stretch content-stretch">
        <SideBar articles={articles} />
        <div className="w-full h-full bg-[#FEEAC2] flex flex-col justify-center content-center text-black">
          <div className="flex flex-col bg-[#d8a640] w-fit mx-auto rounded-md p-4">
            {image && (
              <img
                src={URL.createObjectURL(image)}
                alt="uploaded"
                className="w-64 h-64"
              />
            )}

            {!image && (
              <>
                <input
                  type="file"
                  className="p-2"
                  onChange={handleFileSelect}
                />
                <button
                  className="p-2 w-fit mx-auto bg-gray-600 text-white"
                  onClick={handleUpload}
                >
                  Upload
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
