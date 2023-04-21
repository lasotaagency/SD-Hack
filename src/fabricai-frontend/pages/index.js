import Dropdown from "react-dropdown";
import Image from "next/image";
import { useState } from "react";
import { Spinner } from "react-bootstrap";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [additionalFile, setAdditionalFile] = useState(null);
  const [currImageURL, setCurrImageURL] = useState(null);
  const [prevImageURLs, setPrevImageURLs] = useState([]);
  const [articles, setArticles] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [inputOption, setInputOption] = useState("");
  const [textInput, setTextInput] = useState("");
  const [imageInput, setImageInput] = useState("");

  const baseURI = "https://f034-108-234-21-0.ngrok-free.app";

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleAdditionalFileSelect = (event) => {
    setAdditionalFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
  
    setIsLoading(true);
  
    const formData = new FormData();
    formData.append("file", selectedFile);
  
    try {
      const response = await fetch(`${baseURI}/upload_image`, {
        method: "POST",
        body: formData,
      })
        .then((res) => res.json())
        .then((data) => {
          console.log(data);
          setArticles(data["articles_detected"]);
          setCurrImageURL(baseURI + data["image_url"]);
          // setPrevImageURLs((prevImageURLs) => [
          //   ...prevImageURLs,
          //   baseURI + data["image_url"],
          // ]);
        });
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    console.log("submit");
    setIsLoading(true);

    if (inputOption === "text") {
      console.log(textInput);
      const response = await fetch(
        "https://f034-108-234-21-0.ngrok-free.app/submit",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            image_url: currImageURL,
            condition_data: textInput,
            condition_type: "text",
            option: selectedArticle,
          }),
        }
      )
        .then((res) => res.json())
        .then((data) => {
          const generatedUrl = baseURI + data["generated_images"][0].slice(1);
          const generatedUrl2 = baseURI + data["generated_images"][1].slice(1);
          setPrevImageURLs((prevImageURLs) => [
            ...prevImageURLs,
            generatedUrl,
            generatedUrl2,
          ]);
          setCurrImageURL(generatedUrl2);
        });
    } else if (inputOption === "image") {
      const additionalFormData = new FormData();
      additionalFormData.append("additional_image", additionalFile);
      console.log(additionalFile);

      const response = await fetch(
        "https://f034-108-234-21-0.ngrok-free.app/upload_additional_image",
        {
          method: "POST",
          body: additionalFormData,
        }
      )
        .then((res) => res.json())
        .then((data) => {
          console.log(data);
          console.log("HERE");
          const response = fetch(
            "https://f034-108-234-21-0.ngrok-free.app/submit",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                image_url: currImageURL,
                condition_data:
                  "https://f034-108-234-21-0.ngrok-free.app" +
                  data["image_url"],
                condition_type: "image",
                option: selectedArticle,
              }),
            }
          )
            .then((res) => res.json())
            .then((data) => {
              console.log(data);
              const generatedUrl =
                baseURI + data["generated_images"][0].slice(1);
              const generatedUrl2 =
                baseURI + data["generated_images"][1].slice(1);
              setPrevImageURLs((prevImageURLs) => [
                ...prevImageURLs,
                generatedUrl,
                generatedUrl2,
              ]);
              setCurrImageURL(generatedUrl2);
            });
        });
    }
    setIsLoading(false);
  };

  const handlePreviousImageClick = (index) => {
    // Set the current image URL to the URL of the selected previous image
    const tempCurrImageURL = currImageURL;
    setCurrImageURL(prevImageURLs[index]);
    setPrevImageURLs((prevImageURLs) => [
      ...prevImageURLs.slice(0, index),
      tempCurrImageURL,
      ...prevImageURLs.slice(index + 1),
    ]);
  };

  return (
    <>
      <div className="h-screen w-screen flex flex-row justify-stretch content-stretch">
        <div className="w-[20%] bg-[#088395] flex flex-col content-center text-center relative">
          {articles.length > 0 && (
            <>
              {/* <h3 className="text-[#0A4D68]">Autodetected Clothing Options</h3> */}
              <div className="mt-32">Select a Clothing Options</div>
              <Dropdown
                options={articles}
                className="w-[80%] mt-4 bg-[#D9D9D9] p-2 text-[#0A4D68] mx-auto"
                onChange={(e) => {
                  setSelectedArticle(e.value);
                }}
              />
              <div className="mt-32">
                <div>
                  <label>
                    <input
                      type="radio"
                      value="text"
                      checked={inputOption === "text"}
                      onChange={(e) => setInputOption(e.target.value)}
                    />
                    Text Based Edit
                  </label>
                </div>
                <div>
                  <label>
                    <input
                      type="radio"
                      value="image"
                      checked={inputOption === "image"}
                      onChange={(e) => setInputOption(e.target.value)}
                    />
                    Image Based Edit
                  </label>
                </div>
              </div>
              {inputOption === "text" && (
                <>
                  <input
                    className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto"
                    onChange={(e) => setTextInput(e.target.value)}
                  />
                </>
              )}
              {inputOption === "image" && (
                <>
                  <input
                    type="file"
                    className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto"
                    onChange={handleAdditionalFileSelect}
                  />
                </>
              )}
              <button
                className="w-[80%] bg-[#D9D9D9] p-2 mt-2 text-[#0A4D68] mx-auto"
                onClick={handleSubmit}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Spinner animation="border" size="sm" />
                    <span className="ml-2">Generating...</span>
                  </>
                ) : (
                  "Upload"
                )}
              </button>
            </>
          )}
          <Image
            src={"/public/fabric.ai.png"}
            width={120}
            height={200}
            className="absolute bottom-8 left-0 right-0 ml-auto mr-auto"
          />
        </div>
        <div className="w-full h-full bg-[#FEEAC2] flex flex-col justify-center content-center text-black">
          {currImageURL && (
            <img
              src={currImageURL}
              alt="uploaded"
              className="h-[384px] w-auto mx-auto"
            />
          )}

          {!currImageURL && (
            <>
              <h3 className="text-center">Upload an Image</h3>
              <input type="file" className="p-2 mx-auto" onChange={handleFileSelect} />
              <button
                className={`p-2 w-fit mx-auto text-white ${isLoading ? "bg-red-600" : "bg-gray-600"}`}
                onClick={handleUpload}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Spinner animation="border" size="sm" />
                    <span className="ml-2">Uploading...</span>
                  </>
                ) : (
                  "Upload"
                )}
              </button>
            </>
          )}

          {prevImageURLs.length > 0 && (
            <>
              <h3 className="text-center mt-16">Previous Images</h3>
              <div className="flex flex-wrap justify-center gap-x-4 flex-row-reverse">
                {prevImageURLs.map((url, index) => (
                  <img
                    src={url}
                    alt="uploaded"
                    className="h-[384px] w-auto"
                    onClick={() => handlePreviousImageClick(index)}
                    key={index}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
