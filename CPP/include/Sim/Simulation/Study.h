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
# ifdef __COMPILING_ADSK_SIM_STUDY_CPP__
# define ADSK_SIM_STUDY_API XI_EXPORT
# else
# define ADSK_SIM_STUDY_API
# endif
#else
# define ADSK_SIM_STUDY_API XI_IMPORT
#endif

namespace adsk { namespace sim {
    class LoadCases;
}}

namespace adsk { namespace sim {

/// !!!!! Warning !!!!!
/// ! This is hidden and not officially supported
/// !!!!! Warning !!!!!
/// 
/// Object that represents a study inside a simulation model.
class Study : public core::Base {
public:

    /// The type of study.
    StudyTypes type() const;

    /// The name of the study as displayed in the browser.
    std::string name() const;
    bool name(const std::string& value);

    /// The LoadCases collection that provides access to existing load cases in the study.
    core::Ptr<LoadCases> loadCases() const;

    ADSK_SIM_STUDY_API static const char* classType();
    ADSK_SIM_STUDY_API const char* objectType() const override;
    ADSK_SIM_STUDY_API void* queryInterface(const char* id) const override;
    ADSK_SIM_STUDY_API static const char* interfaceId() { return classType(); }

private:

    // Raw interface
    virtual StudyTypes type_raw() const = 0;
    virtual char* name_raw() const = 0;
    virtual bool name_raw(const char* value) = 0;
    virtual LoadCases* loadCases_raw() const = 0;
};

// Inline wrappers

inline StudyTypes Study::type() const
{
    StudyTypes res = type_raw();
    return res;
}

inline std::string Study::name() const
{
    std::string res;

    char* p= name_raw();
    if (p)
    {
        res = p;
        core::DeallocateArray(p);
    }
    return res;
}

inline bool Study::name(const std::string& value)
{
    return name_raw(value.c_str());
}

inline core::Ptr<LoadCases> Study::loadCases() const
{
    core::Ptr<LoadCases> res = loadCases_raw();
    return res;
}
}// namespace sim
}// namespace adsk

#undef ADSK_SIM_STUDY_API