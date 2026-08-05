import { Routes, Route, Outlet } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Search from "./pages/Search";
import ItemDetail from "./pages/ItemDetail";
import PostItem from "./pages/PostItem";
import MyItems from "./pages/MyItems";
import Profile from "./pages/Profile";

function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/search" element={<Search />} />
        <Route path="/items/:id" element={<ItemDetail />} />
        <Route path="/post" element={<PostItem />} />
        <Route path="/my-items" element={<MyItems />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
    </Routes>
  );
}
