//////////////////////////////////////////////////////////////////////////////
//
// Copyright 2025 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk license
// agreement provided at the time of installation or download, or which
// otherwise accompanies this software.
//
//////////////////////////////////////////////////////////////////////////////

#pragma once
#include "../../Core/Base.h"
#include "../SimTypeDefs.h"
#include <string>

// THIS CLASS WILL BE VISIBLE TO AN API CLIENT.
// THIS HEADER FILE WILL BE GENERATED FROM NIDL.
#include "../../Core/OSMacros.h"

#ifdef SIMXINTERFACE_EXPORTS
# ifdef __COMPILING_ADSK_SIM_LOADCASEITEMS_CPP__
# define ADSK_SIM_LOADCASEITEMS_API XI_EXPORT
# else
# define ADSK_SIM_LOADCASEITEMS_API
# endif
#else
# define ADSK_SIM_LOADCASEITEMS_API XI_IMPORT
#endif

namespace adsk { namespace sim {
    class SimAttribute;
}}

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Provides access to a collection of items in a load case.
class LoadCaseItems : public core::Base {
public:

    /// Function that returns the specified item using an index into the collection.
    /// index : The index of the item within the collection to return. The first item in the collection has an index of 0.
    /// Returns the specified item or null if an invalid index was specified.
    core::Ptr<SimAttribute> item(size_t index) const;

    /// Function that returns the specified item by name.
    /// name : The name of the item within the collection to return.
    /// Returns the specified item or null if the name is not found.
    core::Ptr<SimAttribute> itemByName(const std::string& name) const;

    /// The number of items.
    size_t count() const;

    typedef SimAttribute iterable_type;
    template <class OutputIterator> void copyTo(OutputIterator result);

    ADSK_SIM_LOADCASEITEMS_API static const char* classType();
    ADSK_SIM_LOADCASEITEMS_API const char* objectType() const override;
    ADSK_SIM_LOADCASEITEMS_API void* queryInterface(const char* id) const override;
    ADSK_SIM_LOADCASEITEMS_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual SimAttribute* item_raw(size_t index) const = 0;
    virtual SimAttribute* itemByName_raw(const char* name) const = 0;
    virtual size_t count_raw() const = 0;
};

// Inline wrappers

inline core::Ptr<SimAttribute> LoadCaseItems::item(size_t index) const
{
    core::Ptr<SimAttribute> res = item_raw(index);
    return res;
}

inline core::Ptr<SimAttribute> LoadCaseItems::itemByName(const std::string& name) const
{
    core::Ptr<SimAttribute> res = itemByName_raw(name.c_str());
    return res;
}

inline size_t LoadCaseItems::count() const
{
    size_t res = count_raw();
    return res;
}

template <class OutputIterator> inline void LoadCaseItems::copyTo(OutputIterator result)
{
    for (size_t i = 0;i < count();++i)
    {
        *result = item(i);
        ++result;
    }
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_LOADCASEITEMS_API