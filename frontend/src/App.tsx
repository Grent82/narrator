import { Route, Routes } from "react-router-dom";
import { StoriesPage } from "./pages/StoriesPage";
import { StoryPage } from "./pages/StoryPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<StoriesPage />} />
      <Route path="/story/:storyId" element={<StoryPage />} />
    </Routes>
  );
}
